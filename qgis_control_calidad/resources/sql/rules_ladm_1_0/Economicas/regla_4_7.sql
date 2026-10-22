with base as(
select 
distinct
lp.numero_predial
,lu.t_ili_tid  
,lu.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad
--,la.ilicode tipo_anexo
,lc4.ilicode tipo_calificar
,lc3.total_calificacion 
,lc5.ilicode clase_calificacion
,le.ilicode conservacion
,lg.subtotal 
,count(lc5.ilicode) over (partition by lp.numero_predial, lu.identificador,lc5.ilicode) conteo_clase_calif
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}.lc_construcciontipo lc2 on lc2.t_id =lu.tipo_construccion 
left join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion 
left join {esquema}.lc_usouconstipo lu3 on lu3.t_id =lu.uso 
/*left join {esquema}.lc_calificacionnoconvencional lc3 on lc3.lc_unidad_construccion =lc.t_id 
left join {esquema}.lc_anexotipo la on la.t_id =lc3.tipo_anexo 
left join {esquema}.lc_tipologiaconstruccion lt on lt.lc_unidad_construccion =lc.t_id 
left join {esquema}.lc_tipologiatipo lt2 on lt2.t_id =lt.tipo_tipologia */
left join {esquema}.lc_calificacionconvencional lc3 on lc3.lc_unidad_construccion =lu.t_id 
left join {esquema}.lc_calificartipo lc4 on lc4.t_id =lc3.tipo_calificar 
left join {esquema}.lc_grupocalificacion lg on lg.lc_calificacion_convencional =lc3.t_id 
left join {esquema}.lc_clasecalificaciontipo lc5 on lc5.t_id =lg.clase_calificacion 
left join {esquema}.lc_estadoconservaciontipo le on le.t_id =lg.conservacion 
where 1=1
and lc2.ilicode ='Convencional'
--and lu2.ilicode ='Institucional'
and lc3.t_id is not null
order by lp.numero_predial, lu.identificador 
),
tb_cond_4_7 as(
select numero_predial,
identificador,
tipo_calificar,
string_agg(clase_calificacion,',' order by clase_calificacion) items_calificados
from base 
--where numero_predial = '707130100000000130011000000000' and identificador = 'B'  
group by numero_predial,identificador,tipo_calificar),
tb_final as(
select *, 
case when tipo_calificar<>'Industrial' and items_calificados='Acabados_Principales,Banio,Cocina,Estructura' then 'OK'
when  tipo_calificar='Industrial' and items_calificados='Acabados_Principales,Estructura,Complemento_Industria' then 'Ok' else 'Fail' end as cond_4_7
from tb_cond_4_7
)
select * from tb_final where cond_4_7='Fail'
