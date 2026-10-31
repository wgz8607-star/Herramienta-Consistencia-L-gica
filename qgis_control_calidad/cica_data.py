"""Immutable local CSV snapshots and session-only CICA tables."""
import csv
import hashlib
import json
import re
import tempfile
from pathlib import Path

try:
    from psycopg2 import sql
except ImportError:
    sql = None
from .reference_data import PreparedReference, column_name

TABLES = {
    'Datos Contacto': 'cica_contacto',
    'Datos Predio - Derecho': 'cica_predio_derecho',
    'Predio': 'cica_predio',
    'Datos Propietario': 'cica_propietario',
    'Justificación': 'cica_justificacion',
    'Seguimiento de Control': 'cica_seguimiento_control',
    'Unidad de Construcción': 'cica_unidad_construccion',
}


def prepare_csv(table, filename):
    if table not in TABLES.values():
        raise ValueError('Tabla CICA no reconocida.')
    directory = tempfile.TemporaryDirectory(prefix='qgis_cica_')
    try:
        source = Path(filename)
        # Validate the entire encoding, rather than silently replacing characters.
        encoding = 'utf-8-sig'
        try:
            with source.open(encoding=encoding) as stream:
                for _line in stream:
                    pass
        except UnicodeDecodeError:
            encoding = 'cp1252'
        with source.open(encoding=encoding, newline='') as stream:
            sample = stream.read(65536)
            stream.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
            except csv.Error:
                try:
                    dialect = csv.Sniffer().sniff(sample.splitlines()[0], delimiters=',;\t|')
                except (csv.Error, IndexError):
                    dialect = csv.excel
            reader = csv.reader(stream, dialect, strict=True)
            header = next(reader, [])
            if not header or any(not name.strip() for name in header):
                raise ValueError('El CSV debe tener encabezados no vacíos.')
            columns = tuple(column_name(name, index) for index, name in enumerate(header, 1))
            if len(columns) != len(set(columns)):
                raise ValueError('Hay encabezados duplicados después de normalizarlos.')
            digest = hashlib.sha256(json.dumps(columns).encode())
            target = Path(directory.name) / 'data.csv'
            count = 0
            with target.open('w', encoding='utf-8', newline='') as output:
                writer = csv.writer(output, quoting=csv.QUOTE_ALL)
                for values in reader:
                    if not values or not any(value.strip() for value in values):
                        continue
                    if len(values) != len(columns):
                        raise ValueError(f'Fila {reader.line_num}: número de columnas distinto del encabezado.')
                    if any('\x00' in value for value in values):
                        raise ValueError(f'Fila {reader.line_num}: contiene un carácter nulo no admitido por PostgreSQL.')
                    writer.writerow(values)
                    digest.update(json.dumps(values, ensure_ascii=False).encode())
                    digest.update(b'\n')
                    count += 1
            if not count:
                raise ValueError('El CSV no contiene registros.')
        return PreparedReference(table, source.name, columns, count, digest.hexdigest(), target, directory)
    except Exception:
        directory.cleanup()
        raise


def install_csv(connection, reference, schema, template=None):
    """Use existing PostgreSQL column types when a matching table is available."""
    if reference.kind not in TABLES.values():
        raise ValueError('Tabla CICA no reconocida.')
    if sql is None:
        raise RuntimeError('Se requiere psycopg2 para cargar CSV temporales.')
    with connection.cursor() as cursor:
        cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relname = %s AND c.relkind IN ('r', 'p'))", (schema, reference.kind))
        existing = cursor.fetchone()[0]
        if template:
            from .cica_gdb import layer_definitions
            cursor.execute(sql.SQL('CREATE TEMP TABLE {} ({}) ON COMMIT PRESERVE ROWS').format(sql.Identifier(reference.kind), layer_definitions(template)))
        elif existing:
            # LIKE without INCLUDING DEFAULTS cannot invoke persistent sequences.
            cursor.execute(sql.SQL('CREATE TEMP TABLE {} (LIKE {}.{}) ON COMMIT PRESERVE ROWS').format(
                sql.Identifier(reference.kind), sql.Identifier(schema), sql.Identifier(reference.kind)))
        else:
            definitions = sql.SQL(', ').join(sql.SQL('{} TEXT').format(sql.Identifier(c)) for c in reference.columns)
            cursor.execute(sql.SQL('CREATE TEMP TABLE {} ({}) ON COMMIT PRESERVE ROWS').format(
                sql.Identifier(reference.kind), definitions))
        if existing or template:
            # Extend only the session table; existing column types remain intact.
            for column in reference.columns:
                cursor.execute(sql.SQL('ALTER TABLE pg_temp.{} ADD COLUMN IF NOT EXISTS {} TEXT').format(
                    sql.Identifier(reference.kind), sql.Identifier(column)))
        # Text COPY preserves empty strings. For typed existing schemas, empty values
        # become NULL so optional dates/numbers can be imported correctly.
        query = sql.SQL('COPY pg_temp.{} ({}) FROM STDIN WITH (FORMAT CSV, ENCODING \'UTF8\'{})').format(
            sql.Identifier(reference.kind), sql.SQL(', ').join(sql.Identifier(c) for c in reference.columns),
            sql.SQL(', FORCE_NULL ({})').format(sql.SQL(', ').join(sql.Identifier(c) for c in reference.columns)) if existing or template else sql.SQL(''))
        with reference.csv_path.open(encoding='utf-8', newline='') as stream:
            cursor.copy_expert(query.as_string(connection), stream)


def resolve_csv_tables(query, schema, references, spatial_tables=()):
    """Redirect only the selected CSV tables; all other tables keep their schema."""
    # Never rewrite string constants, comments or dollar-quoted SQL bodies.
    protected = re.compile(r"'(?:''|[^'])*'|--[^\n]*(?:\n|$)|/\*[\s\S]*?\*/|\$\$[\s\S]*?\$\$")
    pieces = []
    offset = 0
    def rewrite(text):
        for table in set(references) | set(spatial_tables):
            if table not in TABLES.values() and (table not in spatial_tables or not re.fullmatch(r'[a-z_][a-z0-9_]*', table)):
                raise ValueError('Tabla CICA no reconocida.')
            schema_token = r'(?:"' + re.escape(schema) + r'"|' + re.escape(schema) + r')'
            table_token = r'(?:"' + re.escape(table) + r'"|' + re.escape(table) + r')'
            pattern = r'(?<![\w."])' + schema_token + r'\s*\.\s*' + table_token + r'(?![\w"])'
            text = re.sub(pattern, 'pg_temp.' + table, text, flags=re.IGNORECASE)
        return text
    for match in protected.finditer(query):
        pieces.extend((rewrite(query[offset:match.start()]), match.group()))
        offset = match.end()
    pieces.append(rewrite(query[offset:]))
    return ''.join(pieces)


def prepare_repository_cica(params, municipality="", stages=(), progress=None):
    """Read all seven CICA tables in one consistent, read-only snapshot."""
    from contextlib import closing
    import psycopg2
    selection = cica_selection(municipality, stages)
    prepared = {}
    selected_predios = set()
    try:
        with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
            connection.set_session(readonly=True, isolation_level='REPEATABLE READ')
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL statement_timeout = '120s'")
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", ('snc_cica_copy',))
                    available = {row[0] for row in cursor.fetchall()}
                missing = set(TABLES.values()) - available
                if missing:
                    raise ValueError('Faltan tablas o permisos de lectura en sentencias.snc_cica_copy: ' + ', '.join(sorted(missing)))
                tables = ['cica_predio'] + [table for table in TABLES.values() if table != 'cica_predio']
                for table_index, table in enumerate(tables, 1):
                    if progress:
                        progress(f'Leyendo {table} ({table_index}/7)…')
                    directory = tempfile.TemporaryDirectory(prefix='qgis_cica_repository_')
                    try:
                        path = Path(directory.name) / 'data.csv'
                        digest = hashlib.sha256()
                        count = 0
                        scanned = 0
                        with connection.cursor(name='snapshot_' + table) as cursor:
                            query = sql.SQL('SELECT * FROM {}.{}').format(sql.Identifier('snc_cica_copy'), sql.Identifier(table))
                            if municipality or stages:
                                with connection.cursor() as fields_cursor:
                                    fields_cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s', ('snc_cica_copy', table))
                                    columns = {row[0] for row in fields_cursor.fetchall()}
                                column = next((name for name in ('numero_predial', 'numero_predial_nacional') if name in columns), None)
                                if not column:
                                    raise ValueError(table + ': no contiene NPN para aplicar el municipio y las etapas. No se leerá sin filtro.')
                                conditions = []
                                if table != 'cica_predio' and not selected_predios:
                                    conditions.append(sql.SQL('FALSE'))
                                if municipality:
                                    conditions.append(sql.SQL('btrim({}::text) LIKE {}').format(sql.Identifier(column), sql.Literal(municipality + '%')))
                                if table == 'cica_predio' and stages:
                                    if 'etapa' not in columns:
                                        raise ValueError('cica_predio: no contiene el campo etapa para filtrar.')
                                    conditions.append(sql.SQL("COALESCE(etapa::text, '') IN ({})").format(sql.SQL(', ').join(sql.Literal(stage) for stage in selection['stages'])))
                                if conditions:
                                    query += sql.SQL(' WHERE {}').format(sql.SQL(' AND ').join(conditions))
                            cursor.execute(query)
                            rows = cursor.fetchmany(1000)
                            columns = tuple(column_name(item.name, index) for index, item in enumerate(cursor.description, 1))
                            if len(set(columns)) != len(columns):
                                raise ValueError(table + ': columnas duplicadas después de normalizarlas.')
                            npn_index = next((columns.index(name) for name in ('numero_predial', 'numero_predial_nacional') if name in columns), None)
                            digest.update(json.dumps(columns).encode())
                            with path.open('w', encoding='utf-8', newline='') as stream:
                                writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
                                while rows:
                                    for row in rows:
                                        scanned += 1
                                        if progress and scanned % 5000 == 0:
                                            progress(f'{table} ({table_index}/7): {scanned:,} registros leídos · {count:,} incluidos'.replace(',', '.'))
                                        key = str(row[npn_index]).strip() if npn_index is not None and row[npn_index] is not None else None
                                        if municipality or stages:
                                            if table == 'cica_predio':
                                                if key is not None:
                                                    selected_predios.add(key)
                                            elif key is None or key not in selected_predios:
                                                continue
                                        values = ['' if value is None else str(value) for value in row]
                                        writer.writerow(values)
                                        digest.update(json.dumps(values, ensure_ascii=False).encode())
                                        digest.update(b'\n')
                                        count += 1
                                    rows = cursor.fetchmany(1000)
                        prepared[table] = PreparedReference(table, 'sentencias.snc_cica_copy.' + table, columns, count, digest.hexdigest(), path, directory)
                    except Exception as error:
                        directory.cleanup()
                        if getattr(error, 'pgcode', None) == '57014':
                            raise ValueError(f'La lectura de {table} excedió el tiempo permitido por el servidor. No se aplicó una copia incompleta. Seleccione un municipio o solicite revisar el rendimiento de esta tabla.') from error
                        raise
        return prepared
    except Exception:
        for reference in prepared.values():
            reference.close()
        raise


def predio_status_summary(snapshot):
    """General counts for the selected CICA predio table, before filters."""
    from collections import Counter
    from .territorial_statistics import classify_status
    if 'estado' not in snapshot.columns:
        return None
    index = snapshot.columns.index('estado')
    counts = Counter()
    with snapshot.csv_path.open(encoding='utf-8', newline='') as stream:
        for row in csv.reader(stream):
            counts[classify_status(row[index] if len(row) > index else None)] += 1
    return {key: counts[key] for key in ('active', 'cancelled', 'other')}


def read_repository_cica_date(params):
    """Read the latest mirror timestamp; never infer it from the local clock."""
    from contextlib import closing
    import psycopg2
    with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection, connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '15s'")
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position", ('snc_cica_crudo', '_control'))
            columns = [row[0] for row in cursor.fetchall()]
            candidates = [name for name in columns if re.sub(r'[^a-z0-9]', '', name.lower()) == 'fechamarca']
            if len(candidates) != 1:
                raise ValueError('No se encontró un campo único fecha_marca en snc_cica_crudo._control, o no tiene permisos de lectura.')
            cursor.execute(sql.SQL('SELECT {} FROM {}.{} WHERE {} IS NOT NULL ORDER BY {} DESC LIMIT 1').format(
                sql.Identifier(candidates[0]), sql.Identifier('snc_cica_crudo'), sql.Identifier('_control'),
                sql.Identifier(candidates[0]), sql.Identifier(candidates[0])))
            row = cursor.fetchone()
            return row[0] if row else None


def cica_selection(municipality='', stages=()):
    if municipality and not re.fullmatch(r'[0-9]{5}', municipality):
        raise ValueError('El DIVIPOLA debe contener cinco dígitos.')
    if any(not isinstance(stage, str) for stage in stages):
        raise ValueError('Las etapas no son válidas.')
    return {'municipality': municipality, 'stages': tuple(sorted(set(stages)))}


def cica_member_predicate(column, selection, namespace):
    """Membership in selected predios; stage restrictions apply through predio."""
    conditions = []
    if selection['municipality']:
        conditions.append(sql.SQL('substring(btrim(numero_predial::text), 1, 5) = {}').format(sql.Literal(selection['municipality'])))
    if selection['stages']:
        conditions.append(sql.SQL("COALESCE(etapa::text, '') IN ({})").format(sql.SQL(', ').join(sql.Literal(stage) for stage in selection['stages'])))
    where = sql.SQL(' AND ').join(conditions) if conditions else sql.SQL('TRUE')
    return sql.SQL('btrim({}::text) IN (SELECT btrim(numero_predial::text) FROM {}.cica_predio WHERE {})').format(
        sql.Identifier(column), sql.Identifier(namespace), where)


def read_repository_cica_options(params):
    from contextlib import closing
    import psycopg2
    with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection, connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '60s'")
            cursor.execute("""SELECT substring(btrim(numero_predial::text), 1, 5),
                COALESCE(etapa::text, ''), count(*) FROM snc_cica_copy.cica_predio
                GROUP BY 1, 2 ORDER BY 1, 2""")
            return cursor.fetchall()


def snapshot_municipalities(snapshot):
    column = next((name for name in ('numero_predial', 'numero_predial_nacional') if name in snapshot.columns), None)
    if column is None:
        raise ValueError('La base CICA seleccionada no contiene un campo NPN.')
    index = snapshot.columns.index(column)
    codes = set()
    with snapshot.csv_path.open(encoding='utf-8', newline='') as stream:
        for row in csv.reader(stream):
            code = row[index].strip()[:5] if len(row) > index else ''
            if re.fullmatch(r'[0-9]{5}', code):
                codes.add(code)
    return sorted(codes)
