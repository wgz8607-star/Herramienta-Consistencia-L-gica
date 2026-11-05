"""Runtime alphanumeric report from an unchanged published CICA statement."""
import re
from .gdb_dependencies import requires_gdb

_PROTECTED=re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|--[^\n]*(?:\n|$)|/\*[\s\S]*?\*/|\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$[\s\S]*?\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$")
NOT_EVALUATED='No evaluado: GDB no cargada'


def alphanumeric_report_sql(statement):
    masked=_PROTECTED.sub(lambda match:' '*len(match.group()),statement)
    start=re.match(r'\s*with\s+tb1\s+as\s*\(',masked,re.I)
    if not start:
        raise ValueError('La estructura del reporte no permite separar sus indicadores de GDB de forma segura.')
    begin=start.end();depth=0;parts=[];offset=begin;end=None
    for token in re.finditer(r'\(|\)|\bunion\s+all\b',masked[begin:],re.I):
        a=begin+token.start();b=begin+token.end();value=token.group().lower()
        if value=='(':depth+=1
        elif value==')':
            if depth==0:
                parts.append((offset,a));end=a;break
            depth-=1
        elif depth==0:
            parts.append((offset,a));offset=b
    if end is None:
        raise ValueError('No se pudo identificar el bloque de indicadores del reporte.')
    rewritten=[];omitted=[];ids=set()
    for a,b in parts:
        branch=statement[a:b]
        match=re.search(r'\bselect\s+(\d+)\s+(?:as\s+)?id\b',masked[a:b],re.I)
        if not match or int(match.group(1)) in ids:
            raise ValueError('El reporte no tiene identificadores únicos reconocibles por indicador.')
        item=int(match.group(1));ids.add(item)
        if requires_gdb(branch):
            omitted.append(item)
            rewritten.append(f'SELECT {item} AS id, NULL::bigint AS cantidad')
        else:rewritten.append(branch)
    result=statement[:begin]+'\nUNION ALL\n'.join(rewritten)+statement[end:]
    if requires_gdb(result):
        raise ValueError('El reporte tiene dependencias de GDB fuera de los indicadores separables.')
    return result,tuple(omitted)


def mark_unevaluated_items(rows,omitted_ids):
    for row in rows:
        key=next((key for key in row if str(key).lower()=='id'),None)
        if key is not None and row[key] in omitted_ids:
            quantity=next((key for key in row if str(key).lower()=='cantidad'),'cantidad')
            row[quantity]=NOT_EVALUATED
    return rows
