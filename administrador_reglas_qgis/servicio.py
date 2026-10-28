"""Repository connections use only credentials supplied by the administrator."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
try:
    import psycopg2
except ImportError:
    psycopg2 = None
from .repositorio import create_template, read_rules, fetch_existing, preview_import, insert_import


def connect(params):
    if psycopg2 is None:
        raise RuntimeError('El Python de QGIS necesita psycopg2 para usar PostgreSQL.')
    arguments = dict(params)
    arguments.setdefault('connect_timeout', 8)
    arguments.setdefault('application_name', 'administrador_reglas_qgis')
    return psycopg2.connect(**arguments)


def fingerprint(filename):
    path = Path(filename)
    before = path.stat()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('El Excel cambió durante la lectura. Guárdelo y vuelva a revisarlo.')
    return digest.hexdigest()


def read_timeout(connection):
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '15s'")


def check_connection(params):
    with closing(connect(params)) as connection:
        connection.set_session(readonly=True)
        with connection:
            read_timeout(connection)
            with connection.cursor() as cursor:
                cursor.execute('SELECT current_database(), current_user')
                return cursor.fetchone()


def inspect_file(params, table, filename, schema='public'):
    original = fingerprint(filename)
    rules = read_rules(filename, replace_by_order=True)
    if fingerprint(filename) != original:
        raise ValueError('El Excel cambió durante la lectura. Guárdelo y vuelva a revisarlo.')
    with closing(connect(params)) as connection:
        connection.set_session(readonly=True)
        with connection:
            read_timeout(connection)
            plan = preview_import(connection, table, rules, schema=schema, catalog_target=True, replace_by_order=True)
    plan.connection_signature = connection_signature(params)
    plan.source_path = str(Path(filename).resolve())
    plan.source_fingerprint = original
    return plan


def export_existing(params, table, filename, schema='public'):
    with closing(connect(params)) as connection:
        connection.set_session(readonly=True)
        with connection:
            read_timeout(connection)
            records = fetch_existing(connection, table, schema=schema, catalog_target=True)
    create_template(filename, records, replacement_mode=True)
    return len(records)


def connection_signature(params):
    return hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()


def apply_plan(params, plan):
    if getattr(plan, 'connection_signature', None) != connection_signature(params):
        raise ValueError('La conexión cambió después de la vista previa. Vuelva a revisar la carga.')
    source = getattr(plan, 'source_path', None)
    if source and fingerprint(source) != plan.source_fingerprint:
        raise ValueError('El Excel cambió después de revisarlo. Vuelva a leerlo antes de cargarlo.')
    with closing(connect(params)) as connection:
        with connection:
            return insert_import(connection, plan)


def list_schemas(params):
    with closing(connect(params)) as connection:
        connection.set_session(readonly=True)
        with connection:
            read_timeout(connection)
            with connection.cursor() as cursor:
                cursor.execute("SELECT nspname FROM pg_namespace WHERE left(nspname, 3) <> 'pg_' AND nspname <> 'information_schema' AND has_schema_privilege(oid, 'USAGE') ORDER BY nspname")
                return [row[0] for row in cursor.fetchall()]


def list_tables(params, schema):
    from .repositorio import COLUMNS
    with closing(connect(params)) as connection:
        connection.set_session(readonly=True)
        with connection:
            read_timeout(connection)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT c.table_name, has_table_privilege(quote_ident(c.table_schema) || '.' || quote_ident(c.table_name), 'INSERT') "
                    "FROM information_schema.columns c JOIN information_schema.tables t "
                    "ON t.table_schema = c.table_schema AND t.table_name = c.table_name "
                    "WHERE c.table_schema = %s AND t.table_type = 'BASE TABLE' AND c.column_name = ANY(%s) "
                    "AND has_table_privilege(quote_ident(c.table_schema) || '.' || quote_ident(c.table_name), 'SELECT') "
                    "GROUP BY c.table_schema, c.table_name HAVING COUNT(DISTINCT c.column_name) = %s ORDER BY c.table_name",
                    (schema, list(COLUMNS), len(COLUMNS)))
                return [(row[0], bool(row[1])) for row in cursor.fetchall()]
