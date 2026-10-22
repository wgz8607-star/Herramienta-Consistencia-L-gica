--regla 3.33
with suma_area_unidad as (
select ruc.codigo
	, ruc.tipo_construccion
	, ruc.identificador
	, round(sum(st_Area(ruc.geom))::numeric, 2) suma_area
	, 'r_unidad_ctm12' capa
	from {esquema}{punto}r_unidad_ctm12 ruc 
	group by ruc.codigo, ruc.identificador, ruc.tipo_construccion
union
	select uuc.codigo
	, uuc.tipo_construccion
	, uuc.identificador
	, round(sum(st_Area(uuc.geom))::numeric, 2) suma_area
	, 'u_unidad_ctm12' capa
	from {esquema}{punto}u_unidad_ctm12 uuc 
	group by uuc.codigo, uuc.identificador, uuc.tipo_construccion
union
	select uui.codigo 
	, uui.tipo_construccion
	, uui.identificador
	, round(sum(st_Area(uui.geom))::numeric, 2) suma_area
	,'u_unidad_informal' capa
	from {esquema}{punto}u_unidad_informal uui 
	group by uui.codigo, uui.identificador, uui.tipo_construccion
union
	select rui.codigo
	, rui.tipo_construccion
	, rui.identificador
	, round(sum(st_Area(rui.geom))::numeric, 2) suma_area
	,'r_unidad_informal' capa
	from {esquema}{punto}r_unidad_informal rui 
	group by rui.codigo, rui.identificador, rui.tipo_construccion
)
select distinct
cuc.numero_predial 
, cuc.construccion_area
, sau.identificador
, sau.tipo_construccion
, sau.suma_area
, sau.capa
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_3_33
from {esquema}{punto}cica_unidad_construccion cuc 
left join suma_area_unidad sau on sau.codigo = cuc.numero_predial and cuc.unidad = sau.identificador
left join {esquema}{punto}cica_predio cp on cp.numero_predial = cuc.numero_predial 
where abs(cuc.construccion_area::numeric - round(sau.suma_area::numeric, 2)) > 0.01 
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
order by cuc.numero_predial , sau.identificador