with
base_0 as(
select 
distinct
lp.numero_predial
,lc.t_ili_tid  
,lc.identificador 
,lc3.t_id tid_calif_conv
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad
--,la.ilicode tipo_anexo
,lc4.ilicode tipo_calificar 
,lc5.ilicode clase_calificacion
,lc3.total_calificacion 
,lg.subtotal 
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_construcciontipo lc2 on lc2.t_id =lc.tipo_construccion 
left join {esquema}{punto}lc_unidadconstrucciontipo lu2 on lu2.t_id =lc.tipo_unidad_construccion 
left join {esquema}{punto}lc_usouconstipo lu3 on lu3.t_id =lc.uso 
left join {esquema}{punto}lc_calificacionconvencional lc3 on lc3.lc_unidad_construccion =lc.t_id 
left join {esquema}{punto}lc_calificartipo lc4 on lc4.t_id =lc3.tipo_calificar 
left join {esquema}{punto}lc_grupocalificacion lg on lg.lc_calificacion_convencional =lc3.t_id 
left join {esquema}{punto}lc_clasecalificaciontipo lc5 on lc5.t_id =lg.clase_calificacion 
left join {esquema}{punto}lc_estadoconservaciontipo le on le.t_id =lg.conservacion 
--left join {esquema}{punto}lc_objetoconstruccion lo on lo.lc_grupo_calificacion =lg.t_id 
--left join {esquema}{punto}lc_objetoconstrucciontipo lo2 on lo2.t_id =lo.tipo_objeto_construccion 
where 1=1
and lc2.ilicode ='Convencional'
--and lu2.ilicode ='Institucional'
and lc3.t_id is not null
order by lp.numero_predial, lc.identificador,lc3.t_id
)
,base as(
select *,sum(subtotal) over (partition by numero_predial, identificador,tid_calif_conv) suma_grupos from base_0
)
,tb_final as
(
select distinct 
numero_predial, 
t_ili_tid,
identificador,
tipo_calificar,
total_calificacion,
suma_grupos
from base)
select *,'Fail' cond_4_25 from tb_final
where suma_grupos <>total_calificacion or suma_grupos is null or suma_grupos=0
order by numero_predial, identificador
