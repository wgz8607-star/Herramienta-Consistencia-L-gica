"""Read-only counts of source predio records, using the same territorial keys as validation."""
import csv
import re
from collections import Counter
from contextlib import closing

import psycopg2
from psycopg2 import sql
from .territorial_scope import NPN_COLUMNS, scope_members, sector_scope


def statistics_from_groups(rows, source=''):
    groups = Counter()
    for raw_prefix, count in rows:
        value = '' if raw_prefix is None else str(raw_prefix).strip()
        prefix = value if re.fullmatch(r'[0-9]{17}', value) else ''
        groups[(sector_scope(value), prefix)] += int(count)
    totals = {key: 0 for key in ('urban', 'rural', 'center', 'unknown')}
    for (category, prefix), count in groups.items():
        totals[category] += count
    return {'groups': dict(groups), 'totals': totals, 'total': sum(totals.values()), 'source': source}


def statistics_from_values(values, source='', unique=False):
    counts = Counter(); seen = set(); row_count = missing = duplicates = 0
    for value in values:
        row_count += 1
        value = '' if value is None else str(value).strip()
        if unique:
            if not value:
                missing += 1
                continue
            if value in seen:
                duplicates += 1
                continue
            seen.add(value)
        counts[value[:17]] += 1
    data = statistics_from_groups(counts.items(), source)
    if unique:
        data.update(counting='unique_npn', row_count=row_count, missing_npn=missing, duplicates=duplicates)
    return data


def included_count(statistics, scope, prefixes=()):
    members = scope_members(scope)
    selected = set(prefixes)
    return sum(count for (category, prefix), count in statistics['groups'].items()
               if (scope == 'all' or category in members) and (not selected or prefix in selected))


def prefix_counts(statistics):
    counts = Counter()
    for (category, prefix), count in statistics['groups'].items():
        if prefix:
            counts[prefix] += count
    return dict(counts)


def unavailable_status(reason):
    return {'active': None, 'cancelled': None, 'other': None, 'method': reason}


def classify_status(value):
    value = '' if value is None else str(value).strip().upper()
    return 'active' if value == 'ACTIVO' else 'cancelled' if value == 'CANCELADO' else 'other'


def read_status_counts(cursor, schema, table, columns, model):
    if 'estado' in columns:
        state = sql.SQL('upper(btrim({}::text))').format(sql.Identifier('estado'))
        cursor.execute(sql.SQL("SELECT COUNT(*) FILTER (WHERE {} = 'ACTIVO'), COUNT(*) FILTER (WHERE {} = 'CANCELADO'), COUNT(*) FILTER (WHERE {} IS NULL OR {} NOT IN ('ACTIVO', 'CANCELADO')) FROM {}").format(
            state, state, state, state, sql.Identifier(schema, table)))
        rows = cursor.fetchall()
        active, cancelled, other = rows[0]
        return {'active': int(active), 'cancelled': int(cancelled), 'other': int(other), 'method': 'Campo estado'}
    if model == 'CICA' or 't_id' not in columns:
        return unavailable_status('No se encontró un campo de estado o una relación de novedades utilizable.')
    needed = {
        'ilc_datosadicionaleslevantamientocatastral': {'t_id', 'ilc_predio'},
        'ilc_estructuranovedadnumeropredial': {'ilc_dtsdcnltmntctstral_novedad_numeros_prediales', 'tipo_novedad'},
        'ilc_estructuranovedadnumeropredial_tipo_novedad': {'t_id', 'ilicode'},
    }
    cursor.execute('SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = %s AND table_name IN %s', (schema, tuple(needed)))
    found = {name: set() for name in needed}
    for name, column in cursor.fetchall():
        if name in found:
            found[name].add(column)
    if any(not fields.issubset(found[name]) for name, fields in needed.items()):
        return unavailable_status('No están disponibles las relaciones de novedades del Modelo Interno.')
    # EXISTS counts each predio row once even when it has several cancellation records.
    cursor.execute(sql.SQL("""SELECT COUNT(*) FILTER (WHERE NOT cancelado), COUNT(*) FILTER (WHERE cancelado)
        FROM (SELECT EXISTS (
          SELECT 1 FROM {} d JOIN {} n ON n.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = d.t_id
          JOIN {} t ON t.t_id = n.tipo_novedad
          WHERE d.ilc_predio = p.t_id AND t.ilicode LIKE 'Cancelacion%'
        ) AS cancelado FROM {} p) estados""").format(
            sql.Identifier(schema, 'ilc_datosadicionaleslevantamientocatastral'),
            sql.Identifier(schema, 'ilc_estructuranovedadnumeropredial'),
            sql.Identifier(schema, 'ilc_estructuranovedadnumeropredial_tipo_novedad'), sql.Identifier(schema, table)))
    active, cancelled = cursor.fetchall()[0]
    return {'active': int(active), 'cancelled': int(cancelled), 'other': 0,
            'method': 'Modelo Interno: novedad Cancelacion%; activo = sin novedad de cancelación'}


def read_source_statistics(params, schema, model, snapshot=None, table_name=None):
    if snapshot is not None:
        column = next((name for name in NPN_COLUMNS if name in snapshot.columns), None)
        if column is None:
            raise ValueError('La tabla de predios no contiene una columna NPN.')
        index = snapshot.columns.index(column)
        status_index = snapshot.columns.index('estado') if 'estado' in snapshot.columns else None
        statuses = Counter()
        def values(rows):
            for row in rows:
                if status_index is not None:
                    statuses[classify_status(row[status_index] if len(row) > status_index else None)] += 1
                yield row[index] if len(row) > index else ''
        with snapshot.csv_path.open(encoding='utf-8', newline='') as stream:
            data = statistics_from_values(values(csv.reader(stream)),
                                          'Base catastral a validar · Temporal · ' + ('cica_predio' if model == 'CICA' else 'ilc_predio'), unique=(model == 'R1'))
        if model != 'R1':
            data['status_counts'] = ({**{key: statuses[key] for key in ('active', 'cancelled', 'other')}, 'method': 'Campo estado'}
                                     if status_index is not None else unavailable_status('La base temporal no tiene campo estado.'))
        return data
    if not schema:
        raise ValueError('Seleccione el esquema a validar o cargue la base catastral CICA antes de leer los datos.')
    table = table_name or ('cica_predio' if model == 'CICA' else 'ilc_predio')
    options = dict(params); options.setdefault('connect_timeout', 8)
    with closing(psycopg2.connect(**options)) as connection:
        connection.set_session(readonly=True)
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '30s'")
            cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s', (schema, table))
            columns = {row[0] for row in cursor.fetchall()}
            column = next((name for name in NPN_COLUMNS if name in columns), None)
            if not column:
                raise ValueError(f'{table}: no se encontró una columna NPN en la tabla seleccionada.')
            if model == 'R1':
                # Deduplicate full NPNs, not 17-digit territorial prefixes.
                npn = sql.SQL("NULLIF(btrim({}::text), '')").format(sql.Identifier(column))
                cursor.execute(sql.SQL('SELECT substring(btrim({}::text), 1, 17), COUNT(DISTINCT {}), COUNT(*), COUNT({}) FROM {} GROUP BY 1').format(
                    sql.Identifier(column), npn, npn, sql.Identifier(schema, table)))
                rows = cursor.fetchall()
                data = statistics_from_groups(((row[0], row[1]) for row in rows), schema + '.' + table)
                data.update(counting='unique_npn', row_count=sum(row[2] for row in rows),
                            missing_npn=sum(row[2] - row[3] for row in rows),
                            duplicates=sum(row[3] - row[1] for row in rows))
                return data
            cursor.execute(sql.SQL('SELECT substring(btrim({}::text), 1, 17), COUNT(*) FROM {} GROUP BY 1').format(
                sql.Identifier(column), sql.Identifier(schema, table)))
            data = statistics_from_groups(cursor.fetchall(), schema + '.' + table)
            try:
                data['status_counts'] = read_status_counts(cursor, schema, table, columns, model)
            except Exception:
                data['status_counts'] = unavailable_status('No fue posible consultar el estado de los predios.')
            return data



def read_filter_statistics(params, schema, model, snapshot=None, r1_snapshot=None,
                           reference_mode='temporary', current_reference=None, repository_params=None):
    """Keep source/R1 counts separate, including independent missing/error states."""
    result = {'source_statistics': None, 'source_error': '', 'r1_statistics': None, 'r1_status': ''}
    try:
        result['source_statistics'] = read_source_statistics(params, schema, model, snapshot)
    except Exception as error:
        result['source_error'] = str(error)
    try:
        if reference_mode == 'temporary':
            if r1_snapshot is None:
                result['r1_status'] = 'R1 temporal no cargado. Cárguelo en Referencias R1/R2 y actualice los datos.'
            else:
                data = read_source_statistics({}, '', 'R1', r1_snapshot)
                data['source'] = 'R1 temporal · ' + r1_snapshot.filename
                result['r1_statistics'] = data
        elif current_reference is None:
            result['r1_status'] = 'Seleccione municipio y fecha en R1 y R2 Vigente y actualice los datos.'
        else:
            from .current_references import NAME, SCHEMA
            table = current_reference.get('tables', {}).get('R1', '')
            expected = f"{current_reference.get('divipola', '')}_{current_reference.get('stamp', '')}_r1"
            if not NAME.fullmatch(table) or table != expected:
                raise ValueError('R1 no está disponible para el municipio y fecha seleccionados.')
            data = read_source_statistics(repository_params, SCHEMA, 'R1', table_name=table)
            data['source'] = 'R1 vigente · ' + SCHEMA + '.' + table + ' · ' + current_reference.get('date', '')
            result['r1_statistics'] = data
    except Exception as error:
        result['r1_status'] = 'No fue posible consultar R1: ' + str(error)
    return result


CICA_STAGE_FIELDS = ('divipola', 'zona', 'total_predios', 'total_reconocido',
                     'total_control_calidad', 'con_areas_geo', 'cargados_snc',
                     'cancelados', 'fecha_actualizacion', 'codigos_npn_existentes')


def read_cica_stages(params):
    """Read the published monitoring view without altering its aggregates."""
    with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection, connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '60s'")
            cursor.execute("""SELECT divipola, zona, total_predios, total_reconocido,
                total_control_calidad, con_areas_geo, cargados_snc, cancelados,
                fecha_actualizacion, codigos_npn_existentes
                FROM snc_cica_copy.vw_seguimiento_predios_2026
                ORDER BY divipola, CASE zona WHEN 'Urbano' THEN 1
                WHEN 'Centro poblado' THEN 2 WHEN 'Rural' THEN 3 ELSE 4 END""")
            return cursor.fetchall()
