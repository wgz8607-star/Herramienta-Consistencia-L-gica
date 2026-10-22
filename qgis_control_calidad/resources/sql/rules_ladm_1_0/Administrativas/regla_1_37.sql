--cond 1_37
with tb_cond_1_37_1 as (
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
)
select 
tb1 .numero_predial
,tb1.area_total_terreno
,tb1.area_matriz_terreno_alfa 
,tb1.area_matriz_terreno_geo 
,case when tb1.area_total_terreno is null then 'Fail'
	when tb1.area_matriz_terreno_alfa is null then 'Fail'
	when tb1.area_matriz_terreno_geo is null then'Fail'
	when tb1.area_total_terreno <> tb1.area_matriz_terreno_alfa then 'Fail'
	when tb1.area_total_terreno <> tb1.area_matriz_terreno_geo then 'Fail'
	else 'Ok' end as cond_1_37
from tb_cond_1_37_1 tb1
