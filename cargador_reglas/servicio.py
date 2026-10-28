"""Repository connections use only credentials supplied by the administrator."""
from contextlib import closing
import hashlib
from pathlib import Path
try:
    import psycopg2
except ImportError:
    psycopg2 = None
from .repositorio import create_template, read_rules, fetch_existing, preview_import, insert_import


def connect(params):
    if psycopg2 is None:
        raise RuntimeError('Falta psycopg2-binary. Ejecute instalar_windows.bat o instale requirements.txt.')
    arguments = dict(params)
    arguments.setdefault('connect_timeout', 8)
    arguments.setdefault('application_name', 'administrador_reglas')
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


def inspect_file(params, table, filename):
    original = fingerprint(filename)
    rules = read_rules(filename)
    if fingerprint(filename) != original:
        raise ValueError('El Excel cambió durante la lectura. Guárdelo y vuelva a revisarlo.')
    with closing(connect(params)) as connection:
        connection.set_session(readonly=True)
        with connection:
            read_timeout(connection)
            plan = preview_import(connection, table, rules)
    plan.source_path = str(Path(filename).resolve())
    plan.source_fingerprint = original
    return plan


def export_existing(params, table, filename):
    with closing(connect(params)) as connection:
        connection.set_session(readonly=True)
        with connection:
            read_timeout(connection)
            records = fetch_existing(connection, table)
    create_template(filename, records)
    return len(records)


def apply_plan(params, plan):
    source = getattr(plan, 'source_path', None)
    if source and fingerprint(source) != plan.source_fingerprint:
        raise ValueError('El Excel cambió después de revisarlo. Vuelva a leerlo antes de cargarlo.')
    with closing(connect(params)) as connection:
        with connection:
            return insert_import(connection, plan)
