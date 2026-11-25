"""Deterministic, read-only renumbering proposal using the selected R1 baseline."""
from collections import defaultdict,Counter
import re
from openpyxl import load_workbook
from .readers import normalized
from .candidates import predio_state


def provisional(value,model):
    return value in '789' if model=='CICA' else value.isascii() and value.isalpha()


def terrain_baselines(r1,take_090x_as_max=False):
    """090x means 0900–0909, and only R1 condition 9 is optional."""
    if take_090x_as_max:return {r['block17']:int(r['max_t']) for r in r1.blocks}
    numbers=getattr(r1,'r1_numbers',())
    if not numbers and r1.blocks:raise ValueError('Vuelva a leer el R1 para calcular los máximos excluyendo terrenos 090x de condición 9.')
    maxima={r['block17']:None for r in r1.blocks}
    for npn in numbers:
        if npn[21]=='9' and npn[17:21].startswith('090'):continue
        block=npn[:17];value=int(npn[17:21])
        maxima[block]=value if maxima.get(block) is None else max(maxima[block],value)
    return maxima


def generate_proposal(candidate_rows,r1,model,take_090x_as_max=False):
    if model not in ('CICA','Modelo Interno'):raise ValueError('Fuente no reconocida.')
    candidate_rows=list(candidate_rows)
    prefix_max={r['prefix13']:int(r['max_m']) for r in r1.prefixes}
    terrain_max=terrain_baselines(r1,take_090x_as_max)
    state_values=defaultdict(set)
    for row in candidate_rows:
        state_values[row[0]].add(predio_state(row[10] if len(row)>10 else row[1] if len(row)==2 else None))
    states={old:next(iter(values)) if len(values)==1 else 'ESTADO INCONSISTENTE' for old,values in state_values.items()}
    blocks=defaultdict(list)
    for old in sorted({r[0] for r in candidate_rows if provisional(r[0][13],model) or provisional(r[0][17],model)}):blocks[old[:17]].append(old)
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
        if baseline is None:
            block_error=('Sin terreno R1 elegible: los 090x de condición 9 están excluidos' if block in terrain_max and not take_090x_as_max else 'Sin referencia R1 de terreno para la manzana/vereda 1–17')
        plots=defaultdict(list)
        for old in olds:plots[old[:21]].append(old)
        for offset,(plot,family) in enumerate(sorted(plots.items()),1):
            error=block_error
            number=baseline+offset if baseline is not None else None
            if number is not None and number>9999:error='Consecutivo de terreno agotado (9999)'
            conditions=Counter(n[21] for n in family)
            # A complete PH/condominio family shares its 1–22 prefix. A condition-2
            # companion shares the terrain with one of the explicitly permitted bases.
            if any(states[n]=='ESTADO INCONSISTENTE' for n in family):error='Estados contradictorios para el mismo NPN en la fuente'
            if any(n[21]=='5' and states[n]!='CANCELADO' for n in family):error='Condición 5 adicional: requiere estado CANCELADO comprobado'
            if conditions['2']>1:error='Solo se admite un compañero de condición 2 por terreno'
            if len(family)>1:
                bases=set(conditions)-{'2','5'}
                if '5' in conditions and not bases:
                    error='Condición 5 adicional sin predio base diferente de condición 2'
                allowed_bases=set('01346789') if '5' in conditions and '2' not in conditions else set('03489')
                if len(bases)>1 or not bases.issubset(allowed_bases):
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
                    'base_t':baseline,'family':plot,'condition':old[21],'predio_state':states[old]})
    existing=set(getattr(r1,'r1_numbers',()))
    targets=Counter(row['new'] for row in output if row['new'])
    for row in output:
        if row['new'] and targets[row['new']]>1:
            row.update(new='',status='Pendiente',reason='Colisión de NPN definitivos entre provisionales')
        elif row['new'] and row['new'] in existing:
            row.update(new='',status='Pendiente',reason='El NPN definitivo ya existe en el R1')
    return sorted(output,key=lambda row:row['old'])


def read_comparison(filename,sheet=None):
    """Column A = definitive; column B = provisional. Never coerce Excel numbers."""
    book=load_workbook(filename,read_only=True,data_only=True)
    rows=[];invalid=[]
    try:
        worksheet=book[sheet] if sheet else book[book.sheetnames[0]]
        worksheet.reset_dimensions()  # Some exporters declare A1 despite having thousands of rows.
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


def compare_proposal(proposal,file_rows,only_provisionals=False):
    expected={row['old']:row for row in proposal};found=defaultdict(list)
    for row in file_rows:found[row['old']].append(row)
    final_counts=Counter(row['new'] for row in file_rows)
    result=[]
    for old in sorted(set(expected) if only_provisionals else set(expected)|set(found)):
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
                           'status':status,'reason':reason,'line':entry['line'] if entry else '', 'predio_state':target.get('predio_state','SIN INFORMACIÓN') if target else 'SIN INFORMACIÓN'})
    return result
