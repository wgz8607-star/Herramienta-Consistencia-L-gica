with base as 
(
select 
lp.numero_predial
,cu.ilicode tipo_predio
,ld2.ilicode tipo_derecho
,li.razon_social 
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}{punto}col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}{punto}col_miembros cm on cm.agrupacion  =ld.interesado_lc_agrupacioninteresados 
left join {esquema}{punto}lc_interesado li on li.t_id =cm.interesado_lc_interesado 
left join {esquema}{punto}lc_grupoetnicotipo lg on lg.t_id =li.grupo_etnico
where  cu.ilicode in ('Predio.Publico.Baldio','Predio.Publico.Ejido')
and ld2.ilicode ='Ocupacion'
union all
select 
lp.numero_predial
,cu.ilicode tipo_predio
,ld2.ilicode tipo_derecho
,li.razon_social 
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}{punto}col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}{punto}lc_interesado li on li.t_id =ld.interesado_lc_interesado 
left join {esquema}{punto}lc_grupoetnicotipo lg on lg.t_id =li.grupo_etnico 
where  cu.ilicode in ('Predio.Publico.Baldio','Predio.Publico.Ejido')
and ld2.ilicode ='Ocupacion'
),
tb_cond_2_12 as(
select *
--,case 
,case when razon_social ilike '%la naci%n%' and razon_social is not null or
razon_social ilike '%municipio%' and razon_social is not null or
razon_social ilike '%Agencia Nacional de Tierras%' and razon_social is not null
then 'Fail' else 'Ok' end as cond_2_12
from base)
select * from tb_cond_2_12
where cond_2_12='Fail'
