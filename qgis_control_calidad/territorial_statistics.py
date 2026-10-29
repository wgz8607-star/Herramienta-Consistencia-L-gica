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


def statistics_from_values(values, source=''):
    counts = Counter(('' if value is None else str(value).strip())[:17] for value in values)
    return statistics_from_groups(counts.items(), source)


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


def read_source_statistics(params, schema, model, snapshot=None, table_name=None):
    if snapshot is not None:
        column = next((name for name in NPN_COLUMNS if name in snapshot.columns), None)
        if column is None:
            raise ValueError('La fuente de predios no contiene una columna NPN.')
        index = snapshot.columns.index(column)
        with snapshot.csv_path.open(encoding='utf-8', newline='') as stream:
            return statistics_from_values((row[index] if len(row) > index else '' for row in csv.reader(stream)),
                                          'Fuente temporal · ' + ('cica_predio' if model == 'CICA' else 'ilc_predio'))
    if not schema:
        raise ValueError('Seleccione el esquema a validar o cargue la fuente CICA antes de leer los datos.')
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
                raise ValueError(f'{table}: no se encontró una columna NPN en la fuente seleccionada.')
            cursor.execute(sql.SQL('SELECT substring(btrim({}::text), 1, 17), COUNT(*) FROM {} GROUP BY 1').format(
                sql.Identifier(column), sql.Identifier(schema, table)))
            return statistics_from_groups(cursor.fetchall(), schema + '.' + table)


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
