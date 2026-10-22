--regla 1.16
with regla as (
select cp.numero_predial 
, cp.destino 
, cp.area_geografica
, cp.area_construido
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_16
from {esquema}{punto}cica_predio cp 
where cp.destino = 'AD'
	and (substring(cp.numero_predial,6,2) <>'00'
	or cp.area_construido <> '0'
	or cp.area_geografica > '500')
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
))
select *
from regla 