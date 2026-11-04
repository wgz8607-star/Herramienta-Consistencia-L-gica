"""Select read-only public R1/R2 from the selected validation connection."""
from contextlib import closing
import psycopg2
from .reference_data import REQUIRED, column_name


PUBLIC_REQUIRED = {'R1': {'numero_predial', 'area_terreno'}, 'R2': REQUIRED['R2']}


def normalize_public_columns(columns):
    result = list(columns)
    if 'area_terreno' not in result and 'areaterreno' in result:
        result[result.index('areaterreno')] = 'area_terreno'
    return tuple(result)


def read_public_catalog(params):
    with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection, connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '15s'")
            cursor.execute("SELECT c.table_name, c.column_name FROM information_schema.columns c JOIN information_schema.tables t ON t.table_schema=c.table_schema AND t.table_name=c.table_name WHERE c.table_schema='public' AND t.table_type IN ('BASE TABLE','VIEW','FOREIGN TABLE') ORDER BY c.table_name,c.ordinal_position")
            tables = {}
            for table, column in cursor.fetchall():
                tables.setdefault(table, []).append(column_name(column, 1))
    return {kind: [table for table, columns in tables.items()
                   if len(columns) == len(set(columns)) and required <= set(normalize_public_columns(columns))]
            for kind, required in PUBLIC_REQUIRED.items()}


def prepare_public_references(params, selection):
    from .current_references import prepare_current_references
    return prepare_current_references(params, {'tables': selection}, set(selection), source_schema='public')


def connection_identity(params):
    return tuple(str(params.get(key, '')) for key in ('host', 'port', 'dbname', 'user', 'service'))
