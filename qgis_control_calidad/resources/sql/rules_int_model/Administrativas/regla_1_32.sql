--regla 1.32
with tb_cond_1_32_1 as (
select 
lp.t_id 
,lp.numero_predial_nacional
,ld.area_total_terreno_privada
from {esquema}{punto}ilc_predio lp
left join {esquema}{punto}cr_datosphcondominio ld on ld.ilc_predio =lp.t_id
left join {esquema}{punto}col_uebaunit cu2 on cu2.baunit =lp.t_id and cu2.ue_cr_terreno is not null
left join {esquema}{punto}cr_terreno lt on lt.t_id =cu2.ue_cr_terreno 
where substring(lp.numero_predial_nacional,22,9)='800000000' 
)
,predios_asociados as (
select 
lp.numero_predial_nacional predio_matriz
,sum(coalesce(lp2.area_catastral_terreno,0)) sum_area_terreno_unidades_alfa
,sum(coalesce(st_area(lt.geometria)::numeric,0)) sum_area_terreno_unidades_geo
from {esquema}{punto}ilc_predio lp
inner join tb_cond_1_32_1 tt on tt.t_id=lp.t_id
left join {esquema}{punto}cr_predio_copropiedad lpc on lpc.matriz =lp.t_id 
left join {esquema}{punto}ilc_predio lp2 on lp2.t_id=lpc.unidad_predial
left join {esquema}{punto}col_uebaunit cu2 on cu2.baunit =lpc.unidad_predial and cu2.ue_cr_terreno is not null
left join {esquema}{punto}cr_terreno lt on lt.t_id =cu2.ue_cr_terreno 
group by lp.numero_predial_nacional
),
tb_final as(
select 
tb1 .numero_predial_nacional
,tb1.area_total_terreno_privada
,pa.sum_area_terreno_unidades_alfa 
,round(pa.sum_area_terreno_unidades_geo::numeric,2) as sum_area_terreno_unidades_geo
,case when tb1.area_total_terreno_privada is null then 'Fail'
	when pa.sum_area_terreno_unidades_alfa is null then 'Fail'
	when pa.sum_area_terreno_unidades_geo is null then'Fail'
	when tb1.area_total_terreno_privada <> pa.sum_area_terreno_unidades_alfa then 'Fail'
	when tb1.area_total_terreno_privada <> round(pa.sum_area_terreno_unidades_geo::numeric,2) then 'Fail'
	else 'Ok' end as cond_1_32
from tb_cond_1_32_1 tb1
left join predios_asociados pa on tb1.numero_predial_nacional=pa.predio_matriz
)
select * from tb_final where cond_1_32 ='Fail';