select 
distinct
lp.numero_predial
,lc.identificador  
,lc3.ilicode tipo_calificacion
,lc4.ilicode clase_calif
,le.ilicode conservacion
,'Fail' cond_4_23
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
inner join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
inner join {esquema}{punto}lc_calificacionconvencional lc2 on lc2.lc_unidad_construccion =lc.t_id 
inner join {esquema}{punto}lc_calificartipo lc3 on lc3.t_id =lc2.tipo_calificar 
left join {esquema}{punto}lc_grupocalificacion lg on lg.lc_calificacion_convencional =lc2.t_id 
left join {esquema}{punto}lc_clasecalificaciontipo lc4 on lc4.t_id =lg.clase_calificacion 
left join {esquema}{punto}lc_estadoconservaciontipo le on le.t_id =lg.conservacion 
where 1=1
and lc3.ilicode in ('Comercial','Industrial','Institucional')
and lc4.ilicode in ('Banio','Cocina')
and le.ilicode <>'Malo'
order by lp.numero_predial, lc.identificador
