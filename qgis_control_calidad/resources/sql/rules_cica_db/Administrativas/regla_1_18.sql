

--regla 1.18
with regla as (
select cp.numero_predial 
, cp.destino 
, cp.area_construido
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_18
from {esquema}{punto}cica_predio cp 
where cp.destino in ('R', 'S', 'T') and coalesce(cp.area_construido, '') <> '0'
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
)
select * from 
regla 