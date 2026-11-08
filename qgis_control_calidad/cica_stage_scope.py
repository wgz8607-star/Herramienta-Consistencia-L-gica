"""Optional runtime override of the published control-quality stage scope only."""
import re

_PROTECTED=re.compile(r"'(?:''|[^'])*'|--[^\n]*(?:\n|$)|/\*[\s\S]*?\*/|\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$[\s\S]*?\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$")
_SCOPE=re.compile(r"(?<![\w.])((?:[A-Za-z_][A-Za-z_0-9]*\.)?etapa)\s+IN\s*\(\s*'CONTROL_CALIDAD_(?:GENERAL|GRUPO)'\s*,\s*'CONTROL_CALIDAD_(?:GENERAL|GRUPO)'\s*\)",re.I)
DEFAULT_STAGES={'CONTROL_CALIDAD_GENERAL','CONTROL_CALIDAD_GRUPO'}
MODE_LABELS={'default':'Validación de predios en etapas de control de calidad','custom':'Validación personalizada de etapas','all':'Todas las etapas'}


def apply_stage_scope(statement,selection):
    mode=selection.get('stage_mode','default')
    if mode not in MODE_LABELS:raise ValueError('Modo de etapas CICA no válido.')
    if mode=='default':return statement
    stages=tuple(sorted(set(selection.get('stages',()))))
    if mode=='custom' and not stages:raise ValueError('Seleccione al menos una etapa personalizada.')
    if any(not isinstance(value,str) or '\x00' in value for value in stages):raise ValueError('Etapas CICA no válidas.')
    protected=[(m.start(),m.end()) for m in _PROTECTED.finditer(statement)]
    replacements=[]
    for match in _SCOPE.finditer(statement):
        if any(a<=match.start()<b for a,b in protected):continue
        values=re.findall(r"'([^']*)'",match.group())
        if set(values)!=DEFAULT_STAGES:continue
        if mode=='all':replacement='(TRUE)'
        else:
            literals=["E'"+value.replace('\\','\\\\').replace("'","''")+"'" for value in stages]
            replacement="(COALESCE("+match.group(1)+"::text, '') IN ("+', '.join(literals)+'))'
        replacements.append((match.start(),match.end(),replacement))
    result=statement
    for a,b,replacement in reversed(replacements):result=result[:a]+replacement+result[b:]
    return result
