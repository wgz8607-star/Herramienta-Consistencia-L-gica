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
            missing = set(reference.columns) - set(template.columns)
            if missing:
                raise ValueError('CSV y geodatabase tienen columnas incompatibles: ' + ', '.join(sorted(missing)))
            cursor.execute(sql.SQL('CREATE TEMP TABLE {} ({}) ON COMMIT PRESERVE ROWS').format(sql.Identifier(reference.kind), layer_definitions(template)))
        elif existing:
            # LIKE without INCLUDING DEFAULTS cannot invoke persistent sequences.
            cursor.execute(sql.SQL('CREATE TEMP TABLE {} (LIKE {}.{}) ON COMMIT PRESERVE ROWS').format(
                sql.Identifier(reference.kind), sql.Identifier(schema), sql.Identifier(reference.kind)))
        else:
            definitions = sql.SQL(', ').join(sql.SQL('{} TEXT').format(sql.Identifier(c)) for c in reference.columns)
            cursor.execute(sql.SQL('CREATE TEMP TABLE {} ({}) ON COMMIT PRESERVE ROWS').format(
                sql.Identifier(reference.kind), definitions))
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
