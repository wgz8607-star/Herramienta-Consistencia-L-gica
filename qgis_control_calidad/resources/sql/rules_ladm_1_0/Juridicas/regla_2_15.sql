with base as(
select 
lp.numero_predial 
,cu.ilicode tipo_predio
,lc.ilicode condicion_predio
,ld2.ilicode derecho_tipo
,case when ld2.ilicode ='Dominio' then 'Ok' else 'Fail' end as cond_2_15
from {esquema}.lc_predio lp 
left join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
left join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}.lc_derecho ld on ld.unidad =lp.t_id 
left join {esquema}.lc_derechotipo ld2 on ld2.t_id =ld.tipo
where cu.ilicode ='Predio.Vacante'
)
select * from base
where cond_2_15 ='Fail'