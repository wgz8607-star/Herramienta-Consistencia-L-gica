--3.8
with areas_geom as (
	select utc.codigo
	, round(coalesce (st_area(utc.geom),0)::decimal,2) area_geom
	, 'u_terreno_ctm12' capa
	from {esquema}{punto}u_terreno_ctm12 utc 
union all
	select uti.codigo
	, round(coalesce (st_area(uti.geom),0)::decimal,2) area_geom
	, 'u_terreno_informal' capa
	from {esquema}{punto}u_terreno_informal uti 
union all 
	select rtc.codigo, round(coalesce (st_area(rtc.geom),0)::decimal,2) area_geom
	, 'r_terreno_ctm12' capa
	from {esquema}{punto}r_terreno_ctm12 rtc
union all
	select rti.codigo, round(COALESCE (st_area(rti.geom),0)::decimal,2) area_geom
	, 'r_terreno_informal' capa
	from {esquema}{punto}r_terreno_informal rti 
)
select distinct
cp.numero_predial
, cp.area_geografica::decimal
, ag.area_geom
, ag.capa
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_3_8
from {esquema}{punto}cica_predio cp 
full join areas_geom ag on ag.codigo = cp.numero_predial 
where abs(ag.area_geom - cp.area_geografica::decimal) > 0.01
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')