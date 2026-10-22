with base as(
select 
distinct
lp.numero_predial
,extract (year from  ld.fecha_visita_predial) anio_visita_predial 
,lc.t_id 
,lc.identificador 
,lc.anio_construccion 
,case when lc.anio_construccion is not null and lc.anio_construccion >0 and lc.anio_construccion <= extract (year from  ld.fecha_visita_predial) then 'Ok' else 'Fail' end as cond_3_30
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
left join {esquema}{punto}lc_resultadovisitatipo lr on lr.t_id =ld.resultado_visita 
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_construcciontipo lc2 on lc2.t_id =lc.tipo_construccion 
left join {esquema}{punto}lc_unidadconstrucciontipo lu2 on lu2.t_id =lc.tipo_unidad_construccion 
left join {esquema}{punto}lc_usouconstipo lu3 on lu3.t_id =lc.uso 
where 1=1
order by lp.numero_predial, lc.identificador 
)
select * from base
where cond_3_30 ='Fail'
