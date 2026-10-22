with base as 
(
select 
lp.numero_predial
,cu.ilicode tipo_predio
,ld2.ilicode tipo_derecho
,case when ld2.ilicode <>'Ocupacion' then 'Ok' else 'Fail' end as cond_2_8
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}{punto}col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
where  cu.ilicode ='Predio.Privado'
)
select * from base 
where cond_2_8 ='Fail'