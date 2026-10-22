with base as(
select 
distinct
lp.numero_predial
,lu.t_id  
,sum(lc2.area_construccion) over (partition by lp.numero_predial, lu.t_id) sum_area_construccion
,sum(lu.area_construida)  over (partition by lp.numero_predial, lu.t_id) sum_area_construida_uc
,sum(lu.area_privada_construida)  over (partition by lp.numero_predial, lu.t_id) sum_area_privada_construida
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}.lc_construccion lc2 on lc2.t_id =lu.lc_construccion 
where 1=1
order by lp.numero_predial
),
tb_cond_3_33 as(
select * 
,case when sum_area_construccion <> (sum_area_construida_uc+sum_area_privada_construida) then 'Fail' else 'Ok' end as cond_3_33
from base
)
select * from tb_cond_3_33
where cond_3_33 ='Fail'
