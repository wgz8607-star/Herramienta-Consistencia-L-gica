--regla 1.28
with tb_cond_1_28_1 as (
select 
lp.t_id 
,lp.numero_predial_nacional
,ld.area_total_construida_comun area_total_construida_comun_matriz_alfa
from {esquema}{punto}ilc_predio lp
left join {esquema}{punto}cr_datosphcondominio ld on ld.ilc_predio =lp.t_id
left join {esquema}{punto}col_uebaunit cu2 on cu2.baunit =lp.t_id 
and cu2.ue_cr_terreno is not null
left join {esquema}{punto}cr_terreno lt on lt.t_id =cu2.ue_cr_terreno 
where substring(lp.numero_predial_nacional,22,9)='900000000' 
),
predios_asociados_uc as (
select 
distinct 
lp2.t_id tid_unidad_predial,
lp2.numero_predial_nacional predio_matriz, 
lc.t_id,
coalesce(lc.identificador, '-') identificador,
coalesce(lc.area_construida,0) area_c 
from {esquema}{punto}ilc_predio lp2
inner join tb_cond_1_28_1 tt on tt.numero_predial_nacional = lp2.numero_predial_nacional
left join {esquema}{punto}col_uebaunit cu on cu.baunit=lp2.t_id and cu.ue_cr_unidadconstruccion is not null
left join {esquema}{punto}cr_unidadconstruccion lu on lu.t_id =cu.ue_cr_unidadconstruccion
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion lc on lc.t_id =lu.cr_caracteristicasunidadconstruccion
)
,areas_uc as(
select predio_matriz, 
sum(area_c) suma_area_constr_comun
from predios_asociados_uc
group by predio_matriz
)
,tb_final as(
select 
tb1.numero_predial_nacional
,tb1.area_total_construida_comun_matriz_alfa
,a.suma_area_constr_comun
,case 
when tb1.area_total_construida_comun_matriz_alfa is null then 'Fail'
when tb1.area_total_construida_comun_matriz_alfa <> a.suma_area_constr_comun then 'Fail'
when tb1.area_total_construida_comun_matriz_alfa = a.suma_area_constr_comun then 'Ok'
else 'fail' 
end as cond_1_28
from tb_cond_1_28_1 tb1
left join areas_uc a on tb1.numero_predial_nacional=a.predio_matriz
)
select * 
from tb_final 
where cond_1_28 ='Fail';