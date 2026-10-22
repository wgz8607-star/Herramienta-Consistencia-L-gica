--regla 1.35
with tb_cond_1_35_1 as (
select 
lp.t_id 
,lp.numero_predial_nacional
,ld.area_total_construida_privada area_total_construida_privada_matriz_alfa
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
,coalesce(ic.area_privada_construida,0) area_pc
from {esquema}{punto}ilc_predio lp
inner join tb_cond_1_35_1 tt on tt.t_id=lp.t_id
left join {esquema}{punto}cr_predio_copropiedad lpc on lpc.matriz =lp.t_id 
left join {esquema}{punto}ilc_predio lp2 on lp2.t_id=lpc.unidad_predial
left join {esquema}{punto}col_uebaunit cu2 on cu2.baunit =lpc.unidad_predial and cu2.ue_cr_unidadconstruccion is not null
left join {esquema}{punto}cr_unidadconstruccion lt on lt.t_id =cu2.ue_cr_unidadconstruccion
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id=lt.cr_caracteristicasunidadconstruccion
)
,areas_uc as(
select predio_matriz, 
sum(area_pc) suma_areas_c
from predios_asociados_uc pauc
group by predio_matriz
)
,tb_final as(
select 
tb1.numero_predial_nacional
,tb1.area_total_construida_privada_matriz_alfa
,a.suma_areas_c area_total_construida_privada_unidades_prediales
,case when tb1.area_total_construida_privada_matriz_alfa is null then 'Fail'
	  when tb1.area_total_construida_privada_matriz_alfa <> a.suma_areas_c then 'Fail'
	  when tb1.area_total_construida_privada_matriz_alfa = a.suma_areas_c then 'Ok'
	else 'Fail' end as cond_1_35
from tb_cond_1_35_1 tb1
left join areas_uc a on tb1.numero_predial_nacional=a.predio_matriz
)
select * from tb_final where cond_1_35 ='Fail';