"""Identify spatial dependencies without changing published SQL."""
import re

_PROTECTED = re.compile(r"'(?:''|[^'])*'|--[^\n]*(?:\n|$)|/\*[\s\S]*?\*/|\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$[\s\S]*?\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$")
_QUALIFIED = re.compile(r'\{esquema\}(?:\.\{punto\}|\{punto\}\.|\{punto\}|\.)?\s*"?([A-Za-z_][A-Za-z_0-9]*)', re.I)
_SPATIAL_RELATION = re.compile(r'\b(?:FROM|JOIN)\s+(?:(?:"?[A-Za-z_][A-Za-z_0-9]*"?)\s*\.\s*)?"?((?:u|r)_[A-Za-z_0-9]+)', re.I)


def requires_gdb(statement):
    text = _PROTECTED.sub(' ', statement or '')
    tables = [name.lower() for name in _QUALIFIED.findall(text)]
    if any(not name.startswith('cica_') and name not in ('r1','r2','reference_r1','reference_r2') for name in tables):
        return True
    return bool(_SPATIAL_RELATION.search(text) or re.search(r'\bST_[A-Za-z_0-9]+\s*\(|\.\s*"?(?:geom|shape)"?\b|::\s*(?:geometry|geography)\b', text, re.I))


def partition_rules(rules, has_gdb):
    if has_gdb:
        return list(rules), []
    executable, omitted = [], []
    for rule in rules:
        (omitted if requires_gdb(rule[2]) else executable).append(rule)
    return executable, omitted


def omission_description(rules):
    return '\n'.join(f'{component} · {name}' for component, name, _sql, _description in rules)
