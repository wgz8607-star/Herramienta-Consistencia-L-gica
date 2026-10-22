with base as(
select 
lp.numero_predial
,ld.interesado_lc_interesado
,ld.interesado_lc_agrupacioninteresados 
,case when ld.interesado_lc_interesado is null and ld.interesado_lc_agrupacioninteresados is null then 'Fail' else 'Ok' end as cond_2_38
from {esquema}.lc_predio lp
left join {esquema}.lc_derecho ld on lp.t_id =ld.unidad
)
select * from base
where cond_2_38 = 'Fail'
