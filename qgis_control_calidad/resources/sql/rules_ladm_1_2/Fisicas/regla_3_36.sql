with base as(
select 
distinct
lp.numero_predial
,lc2.t_id  t_id_construccion
,lc2.numero_pisos 
,case when lc2.numero_pisos <>0 and lc2.numero_pisos is not null then 'Ok' else 'Fail' end as cond_3_36
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_construccion lc2 on lc2.t_id =lu.lc_construccion 
where 1=1
order by lp.numero_predial
)
select * from base
where cond_3_36 ='Fail'
