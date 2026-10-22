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
,case when (e.valor_via_principal ~ '^[0-9]+$' or e.valor_via_principal is null) and 
			(e.valor_via_generadora ~ '^[0-9]+$' or e.valor_via_generadora is null) and 
			(e.numero_predio ~ '^[0-9]+$' or e.numero_predio is null) and
			(e.nombre_predio ~ '^[a-zA-Z0-9áÁéÉíÍóÓúÚ\sÑñ]+$' or e.nombre_predio is null)
			then 'Ok' 
			else 'Fail' end as cond_1_46
from {esquema}{punto}extdireccion e  
left join {esquema}{punto}lc_predio lp on lp.t_id =e.lc_predio_direccion 
left join {esquema}{punto}extdireccion_tipo_direccion etd on etd.t_id =e.tipo_direccion 
left join {esquema}{punto}extdireccion_clase_via_principal ecvp on ecvp.t_id =e.clase_via_principal 
where etd.ilicode ='Estructurada'
)
select * from base where cond_1_46 ='Fail'
