--regla 1.4
select cp.numero_predial 
, cp.condicion_predio_tipo 
, cp.condicion_predio
, cp.coordinador as coordinador 
, cp.usuario as reconocedor
, 'Fail' cond_1_4
from {esquema}{punto}cica_predio cp 
where cp.condicion_predio_tipo = 'Matriz' and substring(cp.numero_predial, 22, 9) <> '900000000' 
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO'))