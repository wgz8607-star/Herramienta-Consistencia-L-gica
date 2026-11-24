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


def model_schemas(params):
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection,connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='30s'")
            cursor.execute("SELECT DISTINCT table_schema FROM information_schema.columns WHERE lower(table_name)='ilc_predio' AND lower(column_name) IN ('numero_predial','numero_predial_nacional') ORDER BY 1")
            return [row[0] for row in cursor.fetchall()]


def source_records(params,model,schema,municipality=''):
    expected='cica_predio' if model=='CICA' else 'ilc_predio'
    if model=='CICA' and (schema!='snc_cica_copy' or params.get('dbname')!='sentencias'):
        raise ValueError('La copia CICA debe consultarse en sentencias.snc_cica_copy.')
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True,isolation_level='REPEATABLE READ')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout='90s'")
                cursor.execute("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema=%s AND lower(table_name)=%s AND lower(column_name) IN ('numero_predial','numero_predial_nacional') ORDER BY CASE WHEN lower(column_name)='numero_predial' THEN 0 ELSE 1 END",(schema,expected))
                fields=cursor.fetchall()
                if not fields:raise ValueError('No se encontró '+schema+'.'+expected+' con columna de número predial accesible.')
                table,column=fields[0]
            with connection.cursor(name='provisional_reader') as cursor:
                cursor.itersize=2000
                query=sql.SQL('SELECT {c}::text FROM {s}.{t}').format(c=sql.Identifier(column),s=sql.Identifier(schema),t=sql.Identifier(table))
                args=()
                if municipality:
                    query+=sql.SQL(' WHERE left(trim({}::text),5)=%s').format(sql.Identifier(column));args=(municipality,)
                cursor.execute(query,args)
                for number,row in enumerate(cursor,1):yield number,row[0]
