"""Pure calculations: maxima come exclusively from the selected R1."""
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import re


@dataclass
class Maxima:
    source_rows: int
    unique_npns: int
    duplicates: int
    blanks: int
    invalid: list
    zones: list
    prefixes: list
    blocks: list
    fingerprint: str


def zone_name(code):
    return 'Rural' if code=='00' else 'Urbano' if code=='01' else 'Centro poblado'


def next_code(value):
    return f'{value+1:04d}' if value<9999 else 'AGOTADO (9999)'


def build_maxima(records, progress=None):
    """records contains (source row number, raw NPN); no guessed zero padding."""
    seen=set();invalid=[];blanks=duplicates=count=0
    zones=defaultdict(list);prefixes=defaultdict(list);blocks=defaultdict(list)
    for number,raw in records:
        count+=1
        if progress and count%2000==0:progress(count)
        if raw is None or (isinstance(raw,str) and not raw.strip()):
            blanks+=1;continue
        if not isinstance(raw,str):
            invalid.append((number,str(raw),'NPN numérico en Excel: no se puede garantizar precisión ni ceros iniciales.'));continue
        npn=raw.strip()
        if not re.fullmatch(r'[0-9]{30}',npn):
            invalid.append((number,npn,'Se requiere un NPN de 30 dígitos; no se incluyen códigos provisionales alfanuméricos.'));continue
        if npn in seen:
            duplicates+=1;continue
        seen.add(npn)
        zones[(npn[:5],npn[5:7])].append(npn)
        prefixes[npn[:13]].append(npn)
        blocks[npn[:17]].append(npn)
    zone_rows=[];prefix_rows=[];block_rows=[]
    for (municipality,zone),values in sorted(zones.items()):
        maximum=max(int(n[13:17]) for n in values)
        witness=min(n for n in values if int(n[13:17])==maximum)
        zone_rows.append({'municipality':municipality,'zone':zone,'zone_name':zone_name(zone),'npns':len(values),'prefixes':len({n[:13] for n in values}),'max_m':f'{maximum:04d}','witness':witness})
    for prefix,values in sorted(prefixes.items()):
        maximum=max(int(n[13:17]) for n in values)
        witness=min(n for n in values if int(n[13:17])==maximum)
        prefix_rows.append({'municipality':prefix[:5],'zone':prefix[5:7],'prefix13':prefix,'npns':len(values),'max_m':f'{maximum:04d}','next_m':next_code(maximum),'witness':witness})
    for prefix,values in sorted(blocks.items()):
        maximum=max(int(n[17:21]) for n in values)
        witness=min(n for n in values if int(n[17:21])==maximum)
        block_rows.append({'municipality':prefix[:5],'zone':prefix[5:7],'prefix13':prefix[:13],'block17':prefix,'block':prefix[13:17],'npns':len(values),'plots':len({n[17:21] for n in values}),'max_t':f'{maximum:04d}','next_t':next_code(maximum),'witness':witness})
    fingerprint=hashlib.sha256('\n'.join(sorted(seen)).encode()).hexdigest()
    return Maxima(count,len(seen),duplicates,blanks,invalid,zone_rows,prefix_rows,block_rows,fingerprint)


def visible_rows(rows, municipality='', zone='', search='', catalog=None):
    import unicodedata
    def key(text):return ''.join(c for c in unicodedata.normalize('NFKD',str(text).casefold()) if not unicodedata.combining(c))
    catalog=catalog or {};needle=key(search.strip())
    return [row for row in rows if (not municipality or row['municipality']==municipality) and (not zone or row['zone']==zone) and (not needle or needle in key(' '.join(str(v) for v in row.values())+' '+' '.join(catalog.get(row['municipality'],('','')))))]
