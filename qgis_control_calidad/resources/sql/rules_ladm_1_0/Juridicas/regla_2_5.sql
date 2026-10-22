select 
lp.numero_predial
,count(*)::text cantidad_derechos
,ld2.ilicode derecho_tipo
,'Fail' cond_2_5
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
where substring(lp.numero_predial,22,1)<>'2'
and ld2.ilicode ='Dominio'
group by lp.numero_predial,ld2.ilicode
having count(*)>1
union all
select 
lp.numero_predial 
,'n/a' cantidad_derechos 
,ld2.ilicode derecho_tipo
,'Fail' cond_2_5
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
where substring(lp.numero_predial,22,1)='2'
and ld2.ilicode ='Dominio'