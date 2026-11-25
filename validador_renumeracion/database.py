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


def cica_access(cursor):
    """Check the effective identity and privileges in the actual reader session."""
    cursor.execute("""SELECT current_database(), inet_server_addr()::text,
        inet_server_port(), session_user, current_user,
        has_schema_privilege(current_user,
            (SELECT oid FROM pg_namespace WHERE nspname='snc_cica_copy'), 'USAGE'),
        has_table_privilege(current_user,
            (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
             WHERE n.nspname='snc_cica_copy' AND c.relname='cica_predio'), 'SELECT')""")
    database,host,port,session,user,schema_ok,table_ok=cursor.fetchone()
    details=(f'Base: {database} | Servidor: {host}:{port}\n'
             f'Usuario de sesión: {session} | Usuario efectivo: {user}\n'
             f'USAGE snc_cica_copy: {schema_ok} | SELECT cica_predio: {table_ok}')
    if not schema_ok or not table_ok:
        raise ValueError('La conexión real del plugin no tiene acceso a la copia CICA.\n'+details+
                         '\nCompruebe los permisos para este usuario en este servidor y base, y confirme COMMIT.')
    return details


def source_state_expression(cursor,schema,model,columns):
    if model=='CICA':
        return (sql.SQL('{}::text').format(sql.Identifier('p',columns['estado'])) if 'estado' in columns else sql.SQL('NULL::text')),()
    if 't_id' not in columns:return sql.SQL('NULL::text'),()
    needed={
        'ilc_datosadicionaleslevantamientocatastral':{'t_id','ilc_predio'},
        'ilc_estructuranovedadnumeropredial':{'ilc_dtsdcnltmntctstral_novedad_numeros_prediales','tipo_novedad'},
        'ilc_estructuranovedadnumeropredial_tipo_novedad':{'t_id','ilicode'},
    }
    cursor.execute('SELECT table_name,column_name FROM information_schema.columns WHERE table_schema=%s AND lower(table_name)=ANY(%s)',(schema,list(needed)))
    tables={};fields={name:{} for name in needed}
    for table,column in cursor.fetchall():
        name=table.lower()
        if name in fields:tables[name]=table;fields[name][column.lower()]=column
    if any(not names.issubset(fields[table]) for table,names in needed.items()):return sql.SQL('NULL::text'),()
    d,n,t=needed
    expression=sql.SQL("""CASE WHEN EXISTS (
        SELECT 1 FROM {d} d JOIN {n} n ON n.{link}=d.{dtid}
        JOIN {t} t ON t.{ttid}=n.{typeid}
        WHERE d.{predio}=p.{ptid}
        AND translate(lower(coalesce(t.{label}::text,'')), 'áéíóúüñ', 'aeiouun') LIKE %s
        ) THEN 'CANCELADO' ELSE 'ACTIVO' END""").format(
        d=sql.Identifier(schema,tables[d]),n=sql.Identifier(schema,tables[n]),t=sql.Identifier(schema,tables[t]),
        link=sql.Identifier(fields[n]['ilc_dtsdcnltmntctstral_novedad_numeros_prediales']),dtid=sql.Identifier(fields[d]['t_id']),
        ttid=sql.Identifier(fields[t]['t_id']),typeid=sql.Identifier(fields[n]['tipo_novedad']),
        predio=sql.Identifier(fields[d]['ilc_predio']),ptid=sql.Identifier(columns['t_id']),label=sql.Identifier(fields[t]['ilicode']))
    return expression,('%cancelacion%',)


def source_records(params,model,schema,municipality='',zones=None):
    if model=='CICA' and zones is not None and (not zones or set(zones)-{'URBANO','CP','RURAL'}):
        raise ValueError('Seleccione al menos una zona válida para CICA.')
    expected='cica_predio' if model=='CICA' else 'ilc_predio'
    if model=='CICA' and (schema!='snc_cica_copy' or params.get('dbname')!='sentencias'):
        raise ValueError('La copia CICA debe consultarse en sentencias.snc_cica_copy.')
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True,isolation_level='REPEATABLE READ')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout='90s'")
                if model=='CICA':cica_access(cursor)
                cursor.execute("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema=%s AND lower(table_name)=%s AND lower(column_name) IN ('numero_predial','numero_predial_nacional','estado','t_id') ORDER BY CASE WHEN lower(column_name)='numero_predial' THEN 0 ELSE 1 END",(schema,expected))
                fields=cursor.fetchall()
                npn_fields=[(table,column) for table,column in fields if column.lower() in ('numero_predial','numero_predial_nacional')]
                if not npn_fields:raise ValueError('No se encontró '+schema+'.'+expected+' con columna de número predial accesible.')
                table,column=npn_fields[0]
                columns={name.lower():name for name_table,name in fields if name_table==table}
                state_expression,state_args=source_state_expression(cursor,schema,model,columns)
            with connection.cursor(name='provisional_reader') as cursor:
                cursor.itersize=2000
                query=sql.SQL('SELECT {c}::text, {state} AS predio_estado FROM {s}.{t} AS p').format(c=sql.Identifier(column),state=state_expression,s=sql.Identifier(schema),t=sql.Identifier(table))
                filters=[];args=list(state_args)
                if model=='CICA':
                    filters.append(sql.SQL('{}=%s AND {}=%s').format(sql.Identifier('etapa'),sql.Identifier('estado_control')))
                    args.extend(['VALIDADO','DESCARGADO_AL_SNC'])
                if model=='CICA' and zones is not None:
                    patterns={'URBANO':'^01$','RURAL':'^00$','CP':'^(0[2-9]|[1-9][0-9])$'}
                    parts=[]
                    for zone in zones:
                        parts.append(sql.SQL('substring(trim({}::text),6,2) ~ %s').format(sql.Identifier(column)));args.append(patterns[zone])
                    filters.append(sql.SQL('(')+sql.SQL(' OR ').join(parts)+sql.SQL(')'))
                if municipality:
                    filters.append(sql.SQL('left(trim({}::text),5)=%s').format(sql.Identifier(column)));args.append(municipality)
                if filters:query+=sql.SQL(' WHERE ')+sql.SQL(' AND ').join(filters)
                cursor.execute(query,tuple(args))
                for number,row in enumerate(cursor,1):yield number,row[0],row[1] if len(row)>1 else None


def cica_municipalities(params):
    if params.get('dbname')!='sentencias':raise ValueError('La copia CICA se consulta en sentencias.')
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection,connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='90s'")
            details=cica_access(cursor)
            try:
                cursor.execute("SELECT DISTINCT left(trim(numero_predial::text),5) AS codigo FROM snc_cica_copy.cica_predio WHERE etapa=%s AND estado_control=%s AND trim(numero_predial::text) ~ '^[0-9]{30}$' ORDER BY codigo",('VALIDADO','DESCARGADO_AL_SNC'))
                return [row[0] for row in cursor.fetchall()]
            except psycopg2.errors.InsufficientPrivilege as error:
                raise ValueError(str(error)+'\n'+details) from error


def cica_diagnostics(params):
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection,connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='15s'")
            return cica_access(cursor)


def cica_copy_date(params):
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection,connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='15s'")
            cursor.execute('SELECT inicio FROM public.copia_cica_progreso ORDER BY id DESC LIMIT 1')
            row=cursor.fetchone()
            return row[0] if row else None


def cica_zone_codes(params,municipality):
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection,connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='60s'")
            cursor.execute("SELECT DISTINCT substring(trim(numero_predial::text),6,2) FROM snc_cica_copy.cica_predio WHERE etapa=%s AND estado_control=%s AND left(trim(numero_predial::text),5)=%s AND trim(numero_predial::text) ~ '^[0-9]{30}$' ORDER BY 1",('VALIDADO','DESCARGADO_AL_SNC',municipality))
            return [row[0] for row in cursor.fetchall()]


def model_municipalities(params,schema):
    """Read actual municipalities from the selected schema, never guess from its name."""
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection,connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='60s'")
            cursor.execute("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema=%s AND lower(table_name)='ilc_predio' AND lower(column_name) IN ('numero_predial','numero_predial_nacional') ORDER BY CASE WHEN lower(column_name)='numero_predial' THEN 0 ELSE 1 END",(schema,))
            fields=cursor.fetchall()
            if not fields:raise ValueError('El esquema no contiene ILC_Predio con número predial accesible.')
            table,column=fields[0]
            cursor.execute(sql.SQL('SELECT DISTINCT left(btrim({c}::text),5) AS codigo FROM {s}.{t} WHERE length(btrim({c}::text))=30 AND left(btrim({c}::text),5) ~ %s ORDER BY codigo').format(c=sql.Identifier(column),s=sql.Identifier(schema),t=sql.Identifier(table)),('^[0-9]{5}$',))
            return [row[0] for row in cursor.fetchall()]
