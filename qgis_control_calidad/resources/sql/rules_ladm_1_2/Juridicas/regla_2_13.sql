with base as 
(
select 
lp.numero_predial
,cu.ilicode tipo_predio
,ld2.ilicode tipo_derecho
,li2.ilicode interesado_tipo
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}{punto}col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}{punto}col_miembros cm on cm.agrupacion  =ld.interesado_lc_agrupacioninteresados 
left join {esquema}{punto}lc_interesado li on li.t_id =cm.interesado_lc_interesado 
left join {esquema}{punto}lc_interesadotipo li2 on li2.t_id =li.tipo 
left join {esquema}{punto}lc_grupoetnicotipo lg on lg.t_id =li.grupo_etnico
where  cu.ilicode in ('Predio.Publico.Uso_Publico','Predio.Publico.Patrimonial','Predio.Publico.Fiscal')
and ld2.ilicode ='Dominio'
union all
select 
lp.numero_predial
,cu.ilicode tipo_predio
,ld2.ilicode tipo_derecho
,li2.ilicode interesado_tipo
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}{punto}col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}{punto}lc_interesado li on li.t_id =ld.interesado_lc_interesado 
left join {esquema}{punto}lc_interesadotipo li2 on li2.t_id =li.tipo 
left join {esquema}{punto}lc_grupoetnicotipo lg on lg.t_id =li.grupo_etnico 
where  cu.ilicode in ('Predio.Publico.Uso_Publico','Predio.Publico.Patrimonial','Predio.Publico.Fiscal')
and ld2.ilicode ='Dominio'
)
select *,'Fail' cond_2_13 
from base
where interesado_tipo <> 'Persona_Juridica'