with base as 
(
select 
lp.numero_predial
,cu.ilicode tipo_predio
,ld2.ilicode tipo_derecho
,lp.tiene_fmi
,lp.matricula_inmobiliaria 
,case when lp.tiene_fmi =false then 'Fail'
	when lp.tiene_fmi =true and matricula_inmobiliaria is not null then 'OK' end as cond_2_6
from {esquema}.lc_predio lp
left join {esquema}.lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}.lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
where ld2.ilicode ='Dominio'
and cu.ilicode = 'Predio.Privado'
)
select * from base where cond_2_6 ='Fail'