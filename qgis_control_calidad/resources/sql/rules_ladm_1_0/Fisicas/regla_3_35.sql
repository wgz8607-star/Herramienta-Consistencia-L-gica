with base as(
select 
distinct
lp.numero_predial
,lc2.t_id  t_id_construccion
,lc2.numero_pisos 
,lu.planta_ubicacion 
,case when lu.planta_ubicacion <=lc2.numero_pisos then 'Ok' else 'Fail' end as cond_3_35
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}.lc_construccion lc2 on lc2.t_id =lu.lc_construccion 
where 1=1
order by lp.numero_predial
)
select * from base
where cond_3_35 ='Fail'
