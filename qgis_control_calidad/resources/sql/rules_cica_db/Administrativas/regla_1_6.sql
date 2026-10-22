--regla 1.6
select cp.numero_predial 
, cp.condicion_predio_tipo 
, cp.condicion_predio
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_6
from {esquema}{punto}cica_predio cp 
where cp.condicion_predio_tipo = 'Condominio.Matriz' and substring(cp.numero_predial, 22, 9) <> '800000000' 
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
