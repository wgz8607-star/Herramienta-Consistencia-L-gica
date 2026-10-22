--cond 1_36
with tb_cond_1_36_1 as (
select 
lp.t_id 
,lp.numero_predial
,ld.area_total_terreno_privada 
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_datosphcondominio ld on ld.lc_predio =lp.t_id
where substring(lp.numero_predial,22,9)='800000000' 
),
predios_asociados as (
select 
lp.numero_predial predio_matriz
,sum(lt.area_terreno) sum_area_terreno_unidades_alfa
,sum(st_area(lt.geometria)):: numeric sum_area_terreno_unidades_geo
from {esquema}{punto}lc_predio lp
inner join tb_cond_1_36_1 tt on tt.t_id=lp.t_id
left join {esquema}{punto}lc_predio_copropiedad lpc on lpc.matriz =lp.t_id 
left join {esquema}{punto}col_uebaunit cu2 on cu2.baunit =lpc.unidad_predial and cu2.ue_lc_terreno is not null
left join {esquema}{punto}lc_terreno lt on lt.t_id =cu2.ue_lc_terreno 
group by lp.numero_predial
)
select 
tb1 .numero_predial
,tb1.area_total_terreno_privada
,pa.sum_area_terreno_unidades_alfa area_total_condominio_alfa
,pa.sum_area_terreno_unidades_geo area_total_condominio_geo
,case when tb1.area_total_terreno_privada is null then 'Fail'
	when pa.sum_area_terreno_unidades_alfa is null then 'Fail'
	when pa.sum_area_terreno_unidades_geo is null then'Fail'
	when tb1.area_total_terreno_privada <> pa.sum_area_terreno_unidades_alfa then 'Fail'
	when tb1.area_total_terreno_privada <> pa.sum_area_terreno_unidades_geo then 'Fail'
	else 'Ok' end as cond_1_36
from tb_cond_1_36_1 tb1
left join predios_asociados pa on tb1.numero_predial=pa.predio_matriz;
