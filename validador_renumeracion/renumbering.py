"""Deterministic, read-only renumbering proposal using the selected R1 baseline."""
from collections import defaultdict,Counter
import re
from openpyxl import load_workbook
from .readers import normalized


def provisional(value,model):
    return value in '789' if model=='CICA' else value.isascii() and value.isalpha()


def generate_proposal(candidate_rows,r1,model):
    if model not in ('CICA','Modelo Interno'):raise ValueError('Fuente no reconocida.')
    prefix_max={r['prefix13']:int(r['max_m']) for r in r1.prefixes}
    terrain_max={r['block17']:int(r['max_t']) for r in r1.blocks}
    blocks=defaultdict(list)
    for old in sorted({r[0] for r in candidate_rows}):blocks[old[:17]].append(old)
    new_blocks=defaultdict(list)
    for block in blocks:
        if provisional(block[13],model):new_blocks[block[:13]].append(block)
    assigned={};errors={}
    for prefix,values in sorted(new_blocks.items()):
        for offset,block in enumerate(sorted(values),1):
            maximum=prefix_max.get(prefix)
            if maximum is None:errors[block]='Sin referencia R1 para el prefijo 1–13';continue
            if maximum+offset>9999:errors[block]='Consecutivo de manzana/vereda agotado (9999)';continue
            assigned[block]=prefix+f'{maximum+offset:04d}'
    output=[]
    for block,olds in sorted(blocks.items()):
        is_new=provisional(block[13],model)
        target_block=assigned.get(block,block)
        baseline=0 if is_new else terrain_max.get(block)
        block_error=errors.get(block,'')
        if baseline is None:block_error='Sin referencia R1 de terreno para la manzana/vereda 1–17'
        plots=defaultdict(list)
        for old in olds:plots[old[:21]].append(old)
        for offset,(plot,family) in enumerate(sorted(plots.items()),1):
            error=block_error
            number=baseline+offset if baseline is not None else None
            if number is not None and number>9999:error='Consecutivo de terreno agotado (9999)'
            conditions=Counter(n[21] for n in family)
            # A complete PH/condominio family shares its 1–22 prefix. A condition-2
            # companion shares the terrain with one of the explicitly permitted bases.
            if len(family)>1:
                bases=set(conditions)-{'2'}
                if len(bases)>1 or not bases.issubset(set('03489')):
                    error='Terreno repetido: combinación de condiciones no definida'
                elif '2' in conditions and not bases:
                    error='Condición 2 repetida sin predio base 0, 3, 4, 8 o 9'
                elif any(conditions[c]>1 for c in bases if c not in '89'):
                    error='Terreno repetido fuera de PH/condominio o pareja de condición 2'
            for old in family:
                new='' if error else target_block+f'{number:04d}'+old[21:]
                output.append({'old':old,'new':new,'status':'Pendiente' if error else 'Generado',
                    'reason':error or ('Manzana/vereda nueva' if is_new else 'Terreno en manzana/vereda existente'),
                    'prefix13':old[:13],'old_block':block,'new_block':target_block if not block_error else '',
                    'base_m':prefix_max.get(old[:13]),
                    'base_t':baseline,'family':plot,'condition':old[21]})
    targets=Counter(row['new'] for row in output if row['new'])
    for row in output:
        if row['new'] and targets[row['new']]>1:
            row.update(new='',status='Pendiente',reason='Colisión de NPN definitivos entre provisionales')
    return sorted(output,key=lambda row:row['old'])


def read_comparison(filename,sheet=None):
    """Column A = definitive; column B = provisional. Never coerce Excel numbers."""
    book=load_workbook(filename,read_only=True,data_only=True)
    rows=[];invalid=[]
    try:
        worksheet=book[sheet] if sheet else book[book.sheetnames[0]]
        for number,values in enumerate(worksheet.iter_rows(max_col=2,values_only=True),1):
            new,old=values
            if new in (None,'') and old in (None,''):continue
            if number==1 and any(any(word in normalized(v) for word in ('predial','provisional','nuevo','definitivo')) for v in values):continue
            valid_old=isinstance(old,str) and re.fullmatch(r'[0-9A-Za-z]{30}',old.strip())
            valid_new=isinstance(new,str) and re.fullmatch(r'[0-9]{30}',new.strip())
            if not valid_old or not valid_new:
                invalid.append((number,str(new or ''),str(old or ''),'A debe ser NPN definitivo de 30 dígitos y B provisional de 30 caracteres; ambos almacenados como texto.'));continue
            rows.append({'line':number,'old':old.strip(),'new':new.strip()})
    finally:book.close()
    return rows,invalid


def compare_proposal(proposal,file_rows):
    expected={row['old']:row for row in proposal};found=defaultdict(list)
    for row in file_rows:found[row['old']].append(row)
    final_counts=Counter(row['new'] for row in file_rows)
    result=[]
    for old in sorted(set(expected)|set(found)):
        target=expected.get(old);entries=found.get(old,[])
        for entry in entries or [None]:
            actual=entry['new'] if entry else ''
            status='';reason=''
            if len(entries)>1:status='Provisional duplicado en archivo'
            elif entry and final_counts[actual]>1:status='Definitivo duplicado en archivo'
            elif target and not target['new']:status='Pendiente de generar';reason=target['reason']
            elif target and entry is None:status='Falta en archivo'
            elif target and actual==target['new']:status='Coincide'
            elif target:
                status='Diferencia'
                if actual[:13]!=old[:13]:reason='Cambió el prefijo territorial 1–13'
                elif actual[21:]!=old[21:]:reason='Cambió la condición o las posiciones 23–30'
                elif actual[13:17]!=target['new'][13:17]:reason='Consecutivo de manzana/vereda diferente'
                else:reason='Consecutivo de terreno diferente (orden o salto)'
            else:
                status='Sin cambio fuera del alcance' if actual==old else 'Fuera del alcance consultado'
                reason='No corresponde a los provisionales identificados en la fuente seleccionada'
            result.append({'old':old,'expected':target['new'] if target else '', 'actual':actual,
                           'status':status,'reason':reason,'line':entry['line'] if entry else ''})
    return result
