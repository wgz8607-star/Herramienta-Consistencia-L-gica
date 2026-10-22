with base as(
select 
lp.numero_predial 
,cu.ilicode tipo_predio
,lc.ilicode condicion_predio
,ld2.ilicode derecho_tipo
,case when cu.ilicode ='Predio.Publico.Uso_Publico' and ld2.ilicode ='Dominio' then 'Ok' else 'Fail' end as cond_2_14
from {esquema}{punto}lc_predio lp 
left join {esquema}{punto}lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
left join {esquema}{punto}col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id 
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo
where lc.ilicode in('Bien_Uso_Publico','Via')
)
select * from base
where cond_2_14 ='Fail'