with base as(
select 
lp.numero_predial
,lt.area_terreno 
,st_area(lt.geometria)
,abs((lt.area_terreno -st_area(lt.geometria)::numeric)/lt.area_terreno)*100 porcentaje_error
,case when abs((lt.area_terreno -st_area(lt.geometria)::numeric)/lt.area_terreno)*100 > 1 then 'Fail' else 'Ok' end as cond_3_8
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_terreno is not null
inner join {esquema}{punto}lc_terreno lt on lt.t_id =cu.ue_lc_terreno 
)
select * from base
where cond_3_8='Fail'
