with base as 
(
select 
lp.numero_predial
,cu.ilicode tipo_predio
,ld2.ilicode tipo_derecho
,case when ld2.ilicode <>'Posesion' then 'Ok' else 'Fail' end as cond_2_9
from {esquema}.lc_predio lp
left join {esquema}.lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}.lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
where cu.ilicode in ('Predio.Publico.Uso_Publico','Predio.Publico.Patrimonial','Predio.Publico.Fiscal','Predio.Publico.Baldio','Predio.Publico.Ejido'))
select * from base 
where cond_2_9 ='Fail'