"""Identify provisional NPNs without changing or approving renumerations."""
import re
from collections import defaultdict
from .numbering_policy import normalize_cica_prefixes,is_provisional


def predio_state(value):
    return str(value).strip().upper() if value is not None and str(value).strip() else 'SIN INFORMACIÓN'


def identify_candidates(records,model,cica_prefixes='789'):
    if model not in ('CICA','Modelo Interno'):raise ValueError('Fuente no reconocida.')
    cica_prefixes=normalize_cica_prefixes(cica_prefixes)
    seen=set();rows=[];invalid=[];duplicates=total=0;states=defaultdict(set)
    for record in records:
        number,raw=record[:2]
        state=predio_state(record[2] if len(record)>2 else None)
        total+=1
        npn=raw.strip() if isinstance(raw,str) else ''
        if not re.fullmatch(r'[0-9A-Za-z]{30}',npn) or not npn[:13].isdigit() or not npn[21:].isdigit():
            invalid.append((number,str(raw or ''),'NPN de 30 caracteres no válido'));continue
        if model=='CICA' and not npn.isdigit():
            invalid.append((number,npn,'CICA requiere NPN numérico'));continue
        states[npn].add(state)
        if npn in seen:duplicates+=1;continue
        seen.add(npn)
        provisional=lambda value:is_provisional(value,model,cica_prefixes)
        manzana,terreno=provisional(npn[13]),provisional(npn[17])
        if not manzana and not terreno:continue
        kind='Manzana y terreno' if manzana and terreno else 'Manzana' if manzana else 'Terreno'
        pending='Condición '+npn[21]+': revisión especial pendiente' if npn[21] in '89' else 'Provisional identificado'
        rows.append((npn,npn[:5],npn[5:7],npn[:13],npn[13:17],npn[:17],npn[17:21],kind,npn[21],pending))
    rows=[row+(next(iter(states[row[0]])) if len(states[row[0]])==1 else 'ESTADO INCONSISTENTE',) for row in rows]
    return {'total':total,'unique':len(seen),'duplicates':duplicates,'invalid':invalid,'rows':sorted(rows)}


def candidate_statistics(rows):
    """Count unique candidate NPNs, grouped by 1–9 and complete block 1–17."""
    groups={};seen=set()
    for row in rows:
        npn=row[0]
        if npn in seen:continue
        seen.add(npn)
        sector=groups.setdefault(npn[:9],{})
        sector.setdefault(npn[:17],[]).append(npn)
    def counts(prefix,values):
        return {'prefix':prefix,'predios':len(values),'blocks':len({n[:17] for n in values}),
                'plots':len({n[:21] for n in values}),'pending':sum(n[21] in '89' for n in values)}
    result=[]
    for prefix,blocks in sorted(groups.items()):
        item=counts(prefix,[n for values in blocks.values() for n in values])
        item['children']=[counts(block,values) for block,values in sorted(blocks.items())]
        result.append(item)
    return result


def block_name(prefix):
    return 'Vereda' if prefix[5:7]=='00' else 'Manzana'


def new_block_statistics(rows):
    """Only blocks identified as provisional at position 14."""
    groups=candidate_statistics(row for row in rows if row[7] in ('Manzana','Manzana y terreno'))
    return [block for sector in groups for block in sector['children']]


def new_block_groups(rows):
    return candidate_statistics(row for row in rows if row[7] in ('Manzana','Manzana y terreno'))
