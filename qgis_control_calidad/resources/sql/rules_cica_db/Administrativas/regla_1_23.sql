--regla 1.23
with tb1 as (
select cp.numero_predial 
, cp.tiene_area_registral 
, cp.area_registral
, cp.coordinador
, cp.usuario as reconocedor
, case 	when cp.tiene_area_registral = 'SI' and coalesce (NULLIF(cp.area_registral,'')::numeric, 0)::numeric = 0 then 'Fail' 
		when cp.tiene_area_registral = 'NO' and coalesce (NULLIF(cp.area_registral,'')::numeric, -1)::numeric <> 0 then 'Fail'
		else 'Ok' end cond_1_23 
from {esquema}{punto}cica_predio cp 
where cp.estado <> 'CANCELADO'
)
select * from tb1 where cond_1_23 = 'Fail' 
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)