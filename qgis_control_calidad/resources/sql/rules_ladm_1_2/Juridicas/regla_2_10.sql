with base as 
(
select 
lp.numero_predial
,cu.ilicode tipo_predio
,ld2.ilicode tipo_derecho
,li.razon_social 
--,case when ld2.ilicode <>'Posesion' then 'Ok' else 'Fail' end as cond_2_9
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}{punto}col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}{punto}col_miembros cm on cm.agrupacion  =ld.interesado_lc_agrupacioninteresados 
left join {esquema}{punto}lc_interesado li on li.t_id =cm.interesado_lc_interesado 
where cu.ilicode in ('Predio.Publico.Baldio','Predio.Publico.Ejido')
and ld2.ilicode ='Dominio'
union all
select 
lp.numero_predial
,cu.ilicode tipo_predio
,ld2.ilicode tipo_derecho
,li.razon_social 
--,case when ld2.ilicode <>'Posesion' then 'Ok' else 'Fail' end as cond_2_9
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}{punto}col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}{punto}lc_interesado li on li.t_id =ld.interesado_lc_interesado 
where cu.ilicode in ('Predio.Publico.Baldio','Predio.Publico.Ejido')
and ld2.ilicode ='Dominio'
),
tb_cond_2_10 as(
select *
,case when razon_social is null then 'Fail'
	when razon_social is not null and (razon_social ilike '%la naci%n%' or razon_social ilike '%municipio%'  or razon_social ilike '%agencia nacional de tierras%') then 'Ok' else 'Fail' end as cond_2_10
from base 
)
select * from tb_cond_2_10
where cond_2_10='Fail'