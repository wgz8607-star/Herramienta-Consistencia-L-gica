with base as(
select 
distinct
lp.numero_predial
,lc2.t_id  t_id_construccion
,lc2.numero_pisos
,max(lu.planta_ubicacion) over (partition by lc2.t_id) max_pisos
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}.lc_construccion lc2 on lc2.t_id =lu.lc_construccion 
where 1=1
order by lp.numero_predial
),
tb_cond_3_37 as(
select * 
,case when numero_pisos>max_pisos then 'Fail' else 'Ok' end as cond_3_37
from base
)
select * from tb_cond_3_37
where cond_3_37 ='Fail'
