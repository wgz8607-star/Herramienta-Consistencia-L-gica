--3.6
with areas as (
select utc.codigo , st_area(utc.geom) area_geom, 'u_terreno_ctm12' tabla
from {esquema}{punto}u_terreno_ctm12 utc 
union all
select uti.codigo, st_area(uti.geom) area_geom, 'u_terreno_informal' tabla 
from {esquema}{punto}u_terreno_informal uti 
union all 
select rrc.codigo, st_area(rrc.geom) area_geom, 'r_terreno_ctm12' tabla
from {esquema}{punto}r_terreno_ctm12 rrc
union all
select rti.codigo, st_area(rti.geom) area_geom, 'r_terreno_informal' tabla
from {esquema}{punto}r_terreno_informal rti 
)
select codigo
, area_geom
, tabla
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_3_6
from areas 
left join {esquema}{punto}cica_predio cp on areas.codigo = cp.numero_predial 
where area_geom <= 5
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')