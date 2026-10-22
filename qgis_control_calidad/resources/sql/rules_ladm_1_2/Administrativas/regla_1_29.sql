--cond 1_29
with tb_cond_1_29
as 
(
select 
lp.numero_predial
,ld.area_total_terreno 
,ld.area_total_terreno_privada 
,ld.area_total_terreno_comun
,lt.area_terreno
,case when lt.area_terreno <> ld.area_total_terreno 
        or lt.area_terreno <> ld.area_total_terreno_privada 
        or lt.area_terreno <> ld.area_total_terreno_comun 
      then 'Fail' 
      when ld.area_total_terreno is null or ld.area_total_terreno_privada is null or ld.area_total_terreno_comun is null then 'Fail'
      else 'OK' end as cond_1_29
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_datosphcondominio ld on ld.lc_predio =lp.t_id 
left join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_terreno is not null
left join {esquema}{punto}lc_terreno lt on lt.t_id =cu.ue_lc_terreno 
where substring(lp.numero_predial,22,9)='900000000' 
)
select * from tb_cond_1_29
where cond_1_29 ='Fail'
order by numero_predial
;
