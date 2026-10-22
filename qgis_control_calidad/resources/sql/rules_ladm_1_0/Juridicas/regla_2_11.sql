with base as 
(
select 
lp.numero_predial
,cu.ilicode tipo_predio
,lg.ilicode grupo_etnico
--,case when ld2.ilicode <>'Posesion' then 'Ok' else 'Fail' end as cond_2_9
from {esquema}.lc_predio lp
left join {esquema}.lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}.lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}.col_miembros cm on cm.agrupacion  =ld.interesado_lc_agrupacioninteresados 
left join {esquema}.lc_interesado li on li.t_id =cm.interesado_lc_interesado 
left join {esquema}.lc_grupoetnicotipo lg on lg.t_id =li.grupo_etnico
where  cu.ilicode ='Predio.Territorio_Colectivo'
union all
select 
lp.numero_predial
,cu.ilicode tipo_predio
,lg.ilicode grupo_etnico
--,case when ld2.ilicode <>'Posesion' then 'Ok' else 'Fail' end as cond_2_9
from {esquema}.lc_predio lp
left join {esquema}.lc_derecho ld on ld.unidad =lp.t_id
left join {esquema}.lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
left join {esquema}.lc_interesado li on li.t_id =ld.interesado_lc_interesado 
left join {esquema}.lc_grupoetnicotipo lg on lg.t_id =li.grupo_etnico 
where  cu.ilicode ='Predio.Territorio_Colectivo'
)
select *,'Fail' cond_2_11 from base
where grupo_etnico='Ninguno'
