--regla 1.34
with tb_cond_1_34_1 as (
select 
lp.t_id 
,lp.numero_predial_nacional
,ld.area_total_construida area_total_construida_cr_datosphcondominio
from {esquema}{punto}ilc_predio lp
left join {esquema}{punto}cr_datosphcondominio ld on ld.ilc_predio =lp.t_id
left join {esquema}{punto}col_uebaunit cu2 on cu2.baunit =lp.t_id and cu2.ue_cr_terreno is not null
left join {esquema}{punto}cr_terreno lt on lt.t_id =cu2.ue_cr_terreno 
where substring(lp.numero_predial_nacional,22,9)='800000000' 
)
,predios_asociados_uc as (
select 
distinct 
lp.numero_predial_nacional predio_matriz
,lp2.numero_predial_nacional npn_up
,coalesce(ic.identificador,'-') identificador
,coalesce(ic.area_construida,0) area_c 
,coalesce(ic.area_privada_construida,0) area_pc
from {esquema}{punto}ilc_predio lp
inner join tb_cond_1_34_1 tt on tt.t_id=lp.t_id
left join {esquema}{punto}cr_predio_copropiedad lpc on lpc.matriz =lp.t_id 
left join {esquema}{punto}ilc_predio lp2 on lp2.t_id=lpc.unidad_predial
left join {esquema}{punto}col_uebaunit cu2 on cu2.baunit =lpc.unidad_predial and cu2.ue_cr_unidadconstruccion is not null
left join {esquema}{punto}cr_unidadconstruccion lt on lt.t_id =cu2.ue_cr_unidadconstruccion
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id=lt.cr_caracteristicasunidadconstruccion
)
,predio_matriz_uc as (
select
distinct
lp.numero_predial_nacional as predio_matriz2
,coalesce(ic.identificador,'-') identificador
,coalesce(ic.area_construida,0) area_c_matriz
,coalesce(ic.area_privada_construida,0) area_pc_matriz
from {esquema}{punto}cr_unidadconstruccion lt 
left join {esquema}{punto}col_uebaunit cu2 on lt.t_id = cu2.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_predio lp on lp.t_id = cu2.baunit 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = lt.cr_caracteristicasunidadconstruccion 
inner join tb_cond_1_34_1 tt on tt.t_id=lp.t_id
)
,areas_uc as(
select predio_matriz, 
sum(area_c)+sum(area_pc) as suma_areas_c
from predios_asociados_uc pauc
group by predio_matriz
)
,areas_uc_m as(
select predio_matriz2, 
sum(area_c_matriz)+ sum(area_pc_matriz)as suma_areas_c_matriz
from predio_matriz_uc
group by predio_matriz2
)
,tb_final as(
select 
tb1.numero_predial_nacional
,tb1.area_total_construida_cr_datosphcondominio
--,a.suma_areas_c area_total_construida_uc_privada
--,am.suma_areas_c_matriz area_total_construida_uc_comun
,(coalesce(a.suma_areas_c,0) + coalesce(am.suma_areas_c_matriz,0)) as area_total_construida_sum_ilc_caract_uc
,case when tb1.area_total_construida_cr_datosphcondominio is null then 'Fail'
	  when tb1.area_total_construida_cr_datosphcondominio <> (coalesce(a.suma_areas_c,0) + coalesce(am.suma_areas_c_matriz,0)) then 'Fail'
	  when tb1.area_total_construida_cr_datosphcondominio = (coalesce(a.suma_areas_c,0) + coalesce(am.suma_areas_c_matriz,0)) then 'Ok'
	else 'Fail' end as cond_1_34
from tb_cond_1_34_1 tb1
left join areas_uc a on tb1.numero_predial_nacional=a.predio_matriz
left join areas_uc_m am on tb1.numero_predial_nacional=am.predio_matriz2
)
select * from tb_final 
where cond_1_34 ='Fail';