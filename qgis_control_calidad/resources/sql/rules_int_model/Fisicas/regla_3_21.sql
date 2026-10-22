--regla 3.21
with tb1 as (
select ip.numero_predial_nacional npn,
ic2.identificador,
ic.ilicode condicion_predio,
coalesce(ic2.area_privada_construida,0) area_num, 
sum(st_area(cu2.geometria)::numeric) area_geom,
(coalesce(ic2.area_privada_construida,0)-sum(st_area(cu2.geometria)::numeric))/(coalesce(ic2.area_privada_construida,0)+0.00001) indice, --+0.1 para evitar div zero
'Fail' cond_3_21
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id 
inner join {esquema}{punto}cr_unidadconstruccion cu2 on cu2.t_id = cu.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic2 on ic2.t_id = cu2.cr_caracteristicasunidadconstruccion
left join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio 
where ic.ilicode  in ('PH.Unidad_Predial','Condominio.Unidad_Predial')
group by ip.numero_predial_nacional,ic2.identificador,coalesce(ic2.area_privada_construida,0),ic.ilicode
)
select npn,
identificador,
condicion_predio,
area_num,
area_geom,
indice error_porcentual
from tb1 
where indice < -0.1 or indice > 0.1
order by indice;
