"""Session-only territorial views; original source tables are never modified."""
import re
from psycopg2 import sql

SCOPES = {'all': 'Todos', 'urban': 'Urbano (01)', 'rural': 'Rural (00)', 'center': 'Centro poblado (>01)'}
SCOPES.update({'urban+rural': 'Urbano + Rural', 'urban+center': 'Urbano + Centro poblado',
               'rural+center': 'Rural + Centro poblado'})

def scope_members(scope):
    if scope not in SCOPES:
        raise ValueError('Alcance territorial no válido.')
    return ('urban', 'rural', 'center') if scope == 'all' else tuple(scope.split('+'))

def sector_scope(value):
    sector = ('' if value is None else str(value).strip())[5:7]
    if not re.fullmatch(r'[0-9]{2}', sector):
        return 'unknown'
    return 'rural' if sector == '00' else 'urban' if sector == '01' else 'center'

NPN_COLUMNS = ('numero_predial', 'numero_predial_nacional')


def predicate(column, scope, prefixes=()):
    if scope not in SCOPES:
        raise ValueError('Alcance territorial no válido.')
    prefixes = normalize_prefixes(prefixes)
    sector = sql.SQL('substring(btrim({}::text), 6, 2)').format(sql.Identifier(column))
    if scope == 'all':
        result = sql.SQL('TRUE')
    else:
        conditions = []
        for member in scope_members(scope):
            condition = {'urban': " = '01'", 'rural': " = '00'", 'center': " ~ '^[0-9][0-9]$' AND {} > '01'"}[member]
            conditions.append(sql.SQL('({})').format(sector + (sql.SQL(condition).format(sector) if member == 'center' else sql.SQL(condition))))
        result = sql.SQL(' OR ').join(conditions)
    if prefixes:
        values = sql.SQL(', ').join(sql.Literal(value) for value in prefixes)
        result = sql.SQL('({}) AND substring(btrim({}::text), 1, 17) IN ({})').format(result, sql.Identifier(column), values)
    return result


def normalize_prefixes(prefixes):
    values = tuple(sorted(set(prefixes)))
    if any(not isinstance(value, str) or not re.fullmatch(r'[0-9]{17}', value) for value in values):
        raise ValueError('Los códigos de manzana/vereda deben contener exactamente 17 dígitos.')
    return values


def install_scope(connection, schema, temporary_tables, references, scope, prefixes=(), model="CICA", cica_filter=None):
    if scope not in SCOPES:
        raise ValueError('Seleccione el alcance de validación de CICA.')
    prefixes = normalize_prefixes(prefixes)
    cica_filter = cica_filter or {}
    if scope == 'all' and not prefixes and not cica_filter:
        return {}
    sources = set()
    with connection.cursor() as cursor:
        prefix = 'cica_' if model == 'CICA' else 'ilc_'
        predio = prefix + 'predio'
        cursor.execute("SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema = %s AND left(table_name, %s) = %s AND column_name IN ('numero_predial', 'numero_predial_nacional')", (schema, len(prefix), prefix))
        sources.update((schema, row[0]) for row in cursor.fetchall() if row[0] not in temporary_tables)
        sources.update(('pg_temp', name) for name in temporary_tables)
        sources.update(('pg_temp', name) for name in references)
        mapping = {}
        predio_found = False
        for index, (namespace, table) in enumerate(sorted(sources)):
            cursor.execute('SELECT attname FROM pg_attribute WHERE attrelid = to_regclass(%s) AND attnum > 0 AND NOT attisdropped', (sql.Identifier(namespace, table).as_string(connection),))
            columns = {row[0] for row in cursor.fetchall()}
            column = next((name for name in NPN_COLUMNS if name in columns), None)
            if not column:
                if table in references or table == predio:
                    raise ValueError(f'{table}: no tiene una columna NPN para aplicar el alcance.')
                continue
            predio_found |= table == predio
            view = f'validation_scope_{index}'
            condition = predicate(column, scope, prefixes)
            if cica_filter:
                from .cica_data import cica_member_predicate
                if table in references:
                    if cica_filter.get('municipality'):
                        condition = sql.SQL('({}) AND substring(btrim({}::text), 1, 5) = {}').format(condition, sql.Identifier(column), sql.Literal(cica_filter['municipality']))
                else:
                    predio_namespace = 'pg_temp' if predio in temporary_tables else schema
                    condition = sql.SQL('({}) AND ({})').format(condition, cica_member_predicate(column, cica_filter, predio_namespace))
            cursor.execute(sql.SQL('CREATE TEMP VIEW {} AS SELECT * FROM {} WHERE {}').format(
                sql.Identifier(view), sql.Identifier(namespace, table), condition))
            mapping[(namespace, table)] = view
        if not predio_found:
            raise ValueError(f'No se encontró {predio} con NPN para aplicar el filtro territorial.')
    return mapping


def resolve_scope(query, mapping):
    protected = re.compile(r"'(?:''|[^'])*'|--[^\n]*(?:\n|$)|/\*[\s\S]*?\*/|\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$[\s\S]*?\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$")
    def rewrite(text):
        for (namespace, table), view in mapping.items():
            pattern = r'(?<![\w.\"])' + '(?:"' + re.escape(namespace) + '"|' + re.escape(namespace) + r')\s*\.\s*(?:"' + re.escape(table) + '"|' + re.escape(table) + r')(?![\w"])'
            def replace(match):
                # Preserve PostgreSQL's implicit table alias when SQL has no explicit alias.
                tail = text[match.end():].lstrip()
                token = re.match(r'[A-Za-z_][A-Za-z_0-9]*', tail)
                keywords = {'where', 'join', 'left', 'right', 'inner', 'outer', 'full', 'cross',
                            'on', 'group', 'order', 'limit', 'offset', 'union', 'except',
                            'intersect', 'having', 'window', 'fetch', 'for', 'tablesample'}
                implicit = not token or token.group().lower() in keywords
                if tail.startswith('"'):
                    implicit = False
                return 'pg_temp.' + view + (' AS "' + table.replace('"', '""') + '"' if implicit else '')
            text = re.sub(pattern, replace, text, flags=re.I)
        return text
    parts = []; offset = 0
    for match in protected.finditer(query):
        parts.extend((rewrite(query[offset:match.start()]), match.group()))
        offset = match.end()
    parts.append(rewrite(query[offset:]))
    return ''.join(parts)
