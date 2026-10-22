with base as(
select
lp.numero_predial
,lr2.ilicode 
,case when cu.ue_lc_servidumbretransito is null then 'Fail' else 'Ok' end as cond_2_19
from {esquema}{punto}lc_predio lp 
left join {esquema}{punto}lc_restriccion lr on lr.unidad =lp.t_id 
left join {esquema}{punto}lc_restricciontipo lr2 on lr2.t_id=lr.tipo 
left join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_servidumbretransito is not null
where lr2.ilicode='Servidumbre.Transito'
)
select * from base
where cond_2_19 ='Fail'