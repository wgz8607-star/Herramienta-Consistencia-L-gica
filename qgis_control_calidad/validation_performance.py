"""Planner support for tables owned by the current validation session only."""
from psycopg2 import sql

RULE_TIMEOUT_SECONDS = 300
LOCK_TIMEOUT_SECONDS = 15
JOIN_COLUMNS = {'numero_predial', 'numero_predial_nacional', 'codigo', 't_id', 'id_predio', 'predio_id', 'fid', 'objectid'}
NPN_COLUMNS = {'numero_predial', 'numero_predial_nacional'}


def set_query_limits(cursor):
    # LOCAL settings must be repeated after a failed rule rolls back its transaction.
    cursor.execute(f"SET LOCAL statement_timeout = '{RULE_TIMEOUT_SECONDS}s'")
    cursor.execute(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT_SECONDS}s'")


def optimize_temporary_tables(connection, tables, spatial_columns=None, progress=None, use_limits=True):
    spatial_columns = spatial_columns or {}
    for table_index, table in enumerate(sorted(set(tables))):
        if progress: progress(f'Optimizando tabla temporal {table}…')
        with connection.cursor() as cursor:
            if use_limits:
                set_query_limits(cursor)
            target = sql.Identifier('pg_temp', table)
            cursor.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(target))
            columns = {field.name for field in cursor.description or []}
            join_columns = sorted(columns & JOIN_COLUMNS)
            for index, column in enumerate(join_columns):
                name = sql.Identifier(f'validation_join_{table_index}_{index}')
                cursor.execute(sql.SQL('CREATE INDEX {} ON {} ({})').format(name, target, sql.Identifier(column)))
                if column in NPN_COLUMNS:
                    name = sql.Identifier(f'validation_npn_{table_index}_{index}')
                    cursor.execute(sql.SQL('CREATE INDEX {} ON {} ((btrim({}::text)))').format(name, target, sql.Identifier(column)))
            geometry = spatial_columns.get(table)
            if geometry and geometry in columns:
                cursor.execute(sql.SQL('CREATE INDEX {} ON {} USING GIST ({})').format(
                    sql.Identifier(f'validation_geom_{table_index}'), target, sql.Identifier(geometry)))
            statistics_columns = set(join_columns) | (columns & {'estado', 'etapa', 'estado_control'})
            if geometry and geometry in columns: statistics_columns.add(geometry)
            if statistics_columns:
                cursor.execute(sql.SQL('ANALYZE {} ({})').format(target, sql.SQL(', ').join(sql.Identifier(column) for column in sorted(statistics_columns))))
            else:
                cursor.execute(sql.SQL('ANALYZE {}').format(target))
