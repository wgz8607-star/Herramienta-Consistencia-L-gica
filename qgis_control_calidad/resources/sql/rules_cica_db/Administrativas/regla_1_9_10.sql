--regla 1.9_10
select cpd.numero_predial 
, cpd.municipio_codigo 
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_9_10
from {esquema}{punto}cica_predio_derecho cpd 
where coalesce (substring(cpd.numero_predial,1,5),'-')<>coalesce (cpd.municipio_codigo,'+') 
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
