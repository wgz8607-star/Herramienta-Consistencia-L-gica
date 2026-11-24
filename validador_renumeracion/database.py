"""PostgreSQL read-only readers; credentials are taken from QGIS, never bundled."""
from contextlib import closing
import re
import psycopg2
from psycopg2 import sql
from .readers import normalized,NPN_NAMES


def list_tables(params,schema,preloaded=False):
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection,connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='30s'")
            cursor.execute("SELECT c.table_name,c.column_name FROM information_schema.columns c JOIN information_schema.tables t ON t.table_schema=c.table_schema AND t.table_name=c.table_name WHERE c.table_schema=%s AND t.table_type IN ('BASE TABLE','VIEW','FOREIGN TABLE') ORDER BY c.table_name,c.ordinal_position",(schema,))
            found={}
            for table,column in cursor.fetchall():
                if preloaded and not re.fullmatch(r'r1_\d{5}_\d{8}',table):continue
                if normalized(column) in NPN_NAMES and (table not in found or NPN_NAMES.index(normalized(column)) < NPN_NAMES.index(normalized(found[table]))):found[table]=column
            return sorted(found.items())


def database_records(params,schema,table,column):
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True,isolation_level='REPEATABLE READ')
        with connection:
            with connection.cursor() as settings:settings.execute("SET LOCAL statement_timeout='90s'")
            with connection.cursor(name='r1_maxima_reader') as cursor:
                cursor.itersize=2000
                cursor.execute(sql.SQL('SELECT {}::text FROM {}.{}').format(sql.Identifier(column),sql.Identifier(schema),sql.Identifier(table)))
                for number,row in enumerate(cursor,1):yield number,row[0]
