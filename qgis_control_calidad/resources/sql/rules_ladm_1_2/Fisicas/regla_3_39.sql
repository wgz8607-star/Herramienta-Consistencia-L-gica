with base_0 as(
select 
distinct
lp.numero_predial
,round(st_area(lu.geometria)::NUMERIC,1) area_geom
,lu.geometria geom_uc
,lc.t_id 
,lc.identificador 
,lc.area_privada_construida  
,lc.area_construida 
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_construcciontipo lc2 on lc2.t_id =lc.tipo_construccion 
left join {esquema}{punto}lc_unidadconstrucciontipo lu2 on lu2.t_id =lc.tipo_unidad_construccion 
left join {esquema}{punto}lc_usouconstipo lu3 on lu3.t_id =lc.uso 
--where lu3.t_id is not null
order by lp.numero_predial, lc.identificador 
),
base as (
select *
,round(sum(st_area(geom_uc)::numeric) over (partition by numero_predial, identificador) ,1)sum_geom
from base_0
)
select *, 
abs((sum_geom-(coalesce(area_construida,0)+coalesce(area_privada_construida,0)))/(coalesce(area_construida,0)+coalesce(area_privada_construida,0)))*100 porcentaje_error
,'Fail' cond_3_39
from base
where abs((sum_geom-(coalesce(area_construida,0)+coalesce(area_privada_construida,0)))/(coalesce(area_construida,0)+coalesce(area_privada_construida,0)))*100>1
order by numero_predial, identificador
