--regla 1.33
with tb_cond_1_33_1 as (
select 
lp.t_id 
,lp.numero_predial_nacional
,ld.area_total_terreno_comun
,round(coalesce(st_area(lt.geometria)::numeric,0),2) area_geom
,case when round(coalesce(st_area(lt.geometria)::numeric,0),2) <> coalesce(ld.area_total_terreno_comun,0) then 'Fail'
else 'Ok' end as cond_1_33
from {esquema}{punto}ilc_predio lp
left join {esquema}{punto}cr_datosphcondominio ld on ld.ilc_predio =lp.t_id
left join {esquema}{punto}col_uebaunit cu2 on cu2.baunit =lp.t_id and cu2.ue_cr_terreno is not null
left join {esquema}{punto}cr_terreno lt on lt.t_id =cu2.ue_cr_terreno 
where substring(lp.numero_predial_nacional,22,9)='800000000' 
)
select * from tb_cond_1_33_1 where cond_1_33 = 'Fail'
