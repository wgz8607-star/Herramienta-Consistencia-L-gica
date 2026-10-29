"""One displayed cadastral identifier; original query data stays in case identities."""
import re
import unicodedata

PREDIO_HEADER = 'Numero_Predial_Nacional'
ALIASES = ('numeropredialnacional', 'numeropredial', 'npn', 'predio')


def normalized_field(name):
    name = unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', name)


def is_predio_field(name):
    return normalized_field(name) in ALIASES


def predio_value(row):
    normalized = {normalized_field(key): value for key, value in row.items()}
    for name in (*ALIASES, 'codigo'):
        value = normalized.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ''


def rule_sheet_label(rule):
    text = str(rule).strip()
    short = re.sub(r'^regla[\s_.-]*', '', text, flags=re.IGNORECASE)
    return re.sub(r'[.\s]+', '_', short) if re.match(r'^\d+[_.]\d+', short) else text


def rule_sort_key(rule):
    return tuple((0, int(part)) if part.isdigit() else (1, part.casefold())
                 for part in re.split(r'(\d+)', rule_sheet_label(rule)) if part)
