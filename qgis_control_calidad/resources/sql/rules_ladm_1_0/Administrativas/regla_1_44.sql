with base as
(select 
lp.numero_predial
,e.t_id tid_direccion
,etd.ilicode tipo 
,ecvp.ilicode clase_via_principal
,e.valor_via_principal
,e.valor_via_generadora
,e.numero_predio
,e.nombre_predio 
,case when ecvp.ilicode is null or valor_via_principal is null or valor_via_generadora is null or numero_predio is null then 'Fail'
	when nombre_predio is not null then 'Fail'
	when ecvp.ilicode is not null and valor_via_principal is not null and valor_via_generadora is not null and numero_predio is not null and nombre_predio is null then 'Ok' else 'Fail' end as cond_1_44
from {esquema}.extdireccion e  
left join {esquema}.lc_predio lp on lp.t_id =e.lc_predio_direccion 
left join {esquema}.extdireccion_tipo_direccion etd on etd.t_id =e.tipo_direccion 
left join {esquema}.extdireccion_clase_via_principal ecvp on ecvp.t_id =e.clase_via_principal 
where etd.ilicode ='Estructurada'
)
select * from base where cond_1_44 ='Fail';
