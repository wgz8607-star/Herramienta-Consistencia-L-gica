with base as
(
select 
lp.numero_predial
,ld2.ilicode tipo_derecho
,ld.fecha_inicio_tenencia 
,ld3.fecha_visita_predial 
,case when ld3.fecha_visita_predial is not null and (ld.fecha_inicio_tenencia< ld3.fecha_visita_predial) then 'Ok'
when ld3.fecha_visita_predial is null and (ld.fecha_inicio_tenencia< now()) then 'Ok' else 'Fail' end as cond_2_4
from {esquema}.lc_predio lp 
inner join {esquema}.lc_derecho ld on ld.unidad =lp.t_id 
left join {esquema}.lc_derechotipo ld2 on ld2.t_id =ld.tipo
left join {esquema}.lc_datosadicionaleslevantamientocatastral ld3 on ld3.lc_predio =lp.t_id 
--where ld.fecha_inicio_tenencia is not null 
)
select * from base
where cond_2_4 ='Fail'