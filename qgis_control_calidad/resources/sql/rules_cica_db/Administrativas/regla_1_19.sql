--regla 1.19
select cp.numero_predial 
, cp.destino 
, cp.area_construido
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_19
from {esquema}{punto}cica_predio cp 
where cp.destino in ('A', 'B', 'C', 'F', 'G', 'I', 'J', 'X') and coalesce (nullif(cp.area_construido, '')::decimal,0) = 0 
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)