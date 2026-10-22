--regla 1.22
select cp.numero_predial  
, cp.tiene_fmi 
, cp.area_registral 
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_22
from {esquema}{punto}cica_predio cp 
where cp.tiene_fmi = 'NO' and coalesce(cp.area_registral,'') <> '0' 
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)