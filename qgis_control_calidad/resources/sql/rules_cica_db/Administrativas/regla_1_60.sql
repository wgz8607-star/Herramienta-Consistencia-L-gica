--regla 1.60
select cp.numero_predial 
, cp.condicion_predio_tipo 
, cp.direccion 
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_60
from {esquema}{punto}cica_predio cp 
where cp.condicion_predio_tipo = 'PH.Unidad_Predial'
and cp.direccion !~ '(AP|BQ|BD|CS|ED|ET|GA|IN|L|LO|MZ|OF|PQ|PN|TO|UN|UR)'
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')