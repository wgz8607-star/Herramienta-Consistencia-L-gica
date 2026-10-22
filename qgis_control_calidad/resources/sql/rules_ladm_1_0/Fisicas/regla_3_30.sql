with base as(
select 
distinct
lp.numero_predial
,extract (year from  ld.fecha_visita_predial) anio_visita_predial 
,lu.t_id 
,lu.identificador 
,lu.anio_construccion 
,case when lu.anio_construccion is not null and lu.anio_construccion >0 and lu.anio_construccion <= extract (year from  ld.fecha_visita_predial) then 'Ok' else 'Fail' end as cond_3_30
from {esquema}.lc_predio lp
left join {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
left join {esquema}.lc_resultadovisitatipo lr on lr.t_id =ld.resultado_visita 
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}.lc_construcciontipo lc2 on lc2.t_id =lu.tipo_construccion 
left join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion 
left join {esquema}.lc_usouconstipo lu3 on lu3.t_id =lu.uso 
where 1=1
order by lp.numero_predial, lu.identificador 
)
select * from base
where cond_3_30 ='Fail'
