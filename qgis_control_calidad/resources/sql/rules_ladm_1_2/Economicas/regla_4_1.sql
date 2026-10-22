with base as(
select 
distinct
lp.numero_predial
,lc.t_ili_tid  
,lc.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad
,lt2.ilicode tipo_tipologia
,lc4.ilicode tipo_calificar
,lc3.total_calificacion 
,case when lt.t_id is not null or lc3.t_id is not null then 'Ok' else 'Fail' end as cond_4_1
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_construcciontipo lc2 on lc2.t_id =lc.tipo_construccion 
left join {esquema}{punto}lc_unidadconstrucciontipo lu2 on lu2.t_id =lc.tipo_unidad_construccion 
left join {esquema}{punto}lc_usouconstipo lu3 on lu3.t_id =lc.uso 
left join {esquema}{punto}lc_tipologiaconstruccion lt on lt.lc_unidad_construccion =lc.t_id 
left join {esquema}{punto}lc_tipologiatipo lt2 on lt2.t_id =lt.tipo_tipologia 
left join {esquema}{punto}lc_calificacionconvencional lc3 on lc3.lc_unidad_construccion =lc.t_id 
left join {esquema}{punto}lc_calificartipo lc4 on lc4.t_id =lc3.tipo_calificar 
where lc2.ilicode ='Convencional'
order by lp.numero_predial, lc.identificador 
)
select * from base
where cond_4_1='Fail'
