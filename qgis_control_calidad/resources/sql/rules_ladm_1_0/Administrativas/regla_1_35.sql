--cond 1_35
with tb_cond_1_35_1 as (
select 
lp.t_id 
,lp.numero_predial
,ld.area_total_terreno
,lt.area_terreno area_matriz_terreno_alfa
,st_area(lt.geometria):: numeric area_matriz_terreno_geo
from {esquema}.lc_predio lp
left join {esquema}.lc_datosphcondominio ld on ld.lc_predio =lp.t_id
left join {esquema}.col_uebaunit cu2 on cu2.baunit =lp.t_id and cu2.ue_lc_terreno is not null
left join {esquema}.lc_terreno lt on lt.t_id =cu2.ue_lc_terreno 
where substring(lp.numero_predial,22,9)='800000000' 
),
predios_asociados as (
select 
lp.numero_predial predio_matriz
,sum(lt.area_terreno) sum_area_terreno_unidades_alfa
,sum(st_area(lt.geometria)):: numeric sum_area_terreno_unidades_geo
from {esquema}.lc_predio lp
inner join tb_cond_1_35_1 tt on tt.t_id=lp.t_id
left join {esquema}.lc_predio_copropiedad lpc on lpc.copropiedad =lp.t_id 
left join {esquema}.col_uebaunit cu2 on cu2.baunit =lpc.predio and cu2.ue_lc_terreno is not null
left join {esquema}.lc_terreno lt on lt.t_id =cu2.ue_lc_terreno 
group by lp.numero_predial
)
select 
tb1 .numero_predial
,tb1.area_total_terreno
,tb1.area_matriz_terreno_alfa+sum_area_terreno_unidades_alfa area_total_condominio_alfa
,tb1.area_matriz_terreno_geo+sum_area_terreno_unidades_geo area_total_condominio_geo
,case when tb1.area_total_terreno is null then 'Fail'
	when tb1.area_matriz_terreno_alfa+sum_area_terreno_unidades_alfa is null then 'Fail'
	when tb1.area_matriz_terreno_geo+sum_area_terreno_unidades_geo is null then'Fail'
	when tb1.area_total_terreno <> tb1.area_matriz_terreno_alfa+sum_area_terreno_unidades_alfa then 'Fail'
	when tb1.area_total_terreno <> tb1.area_matriz_terreno_geo+sum_area_terreno_unidades_geo then 'Fail'
	else 'Ok' end as cond_1_35
from tb_cond_1_35_1 tb1
left join predios_asociados pa on tb1.numero_predial=pa.predio_matriz;
