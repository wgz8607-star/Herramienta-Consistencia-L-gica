--regla 3.30
with base as (
select cuc.numero_predial 
, cuc.anio_construccion 
, cc.fecha_visita 
, cp.coordinador
, cp.usuario as reconocedor 
, case 	when coalesce (nullif(cuc.anio_construccion, '')::numeric,0) < 1800 then 'Fail' 
		when coalesce (nullif(cuc.anio_construccion, '')::numeric,0) > left(to_timestamp(cc.fecha_visita, 'MM-DD-YYYY')::text, 4)::numeric then 'Fail'
		else 'Ok'
		end cond_3_30
from {esquema}{punto}cica_unidad_construccion cuc 
left join {esquema}{punto}cica_predio cp on cuc.numero_predial = cp.numero_predial 
left join {esquema}{punto}cica_contacto cc on cc.numero_predial = cuc.numero_predial 
where cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
and cp.estado = 'ACTIVO')
select distinct * from base 
where cond_3_30 = 'Fail'