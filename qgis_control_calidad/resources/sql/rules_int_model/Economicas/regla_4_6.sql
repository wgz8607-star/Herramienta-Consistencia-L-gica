
 	--regla 4.6
with cond_4_6 as (
select ip.numero_predial_nacional, cc2.ilicode tipocalificacion, 
case when (coalesce (cc.tamanio_banio,0)+ coalesce (cc.enchape_banio,0)+ coalesce (cc.mobiliario_banio,0)+ coalesce (cc.conservacion_banio,0))>0 then 'Baño con calificacion - Ok' 
	else 'Baño sin calificacion - Fail' end as calif_banio,
case when ctb.ilicode = 'Sin_Banio' and cc.conservacion_banio is null then 'Sin baño - Ok'
	when coalesce (cc.conservacion_banio,0)>0 then 'Baño con conservacion - Ok' 
	else 'Baño sin conservacion - Fail' end as conservacion_banio,
case when (coalesce (cc.tamanio_cocina,0)+ coalesce (cc.enchape_cocina,0)+ coalesce (cc.mobiliario_cocina,0)+ coalesce (cc.conservacion_cocina,0))>0 then  'Cocina con calificacion - Ok' 
	else 'Cocina sin calificacion - Fail' end as calif_cocina,
case  when ctc.ilicode = 'Sin_Cocina' and cc.conservacion_cocina is null then 'Sin cocina - Ok'
	when coalesce(cc.conservacion_cocina,0)>0 then 'Cocina con conservacion - Ok' 
	else 'Cocina sin conservacion - Fail' end as conservacion_cocina,
'Fail' cond_4_6
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu ON cu.baunit = ip.t_id 
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu.ue_cr_unidadconstruccion = cu2.t_id 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu2.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id 
left join {esquema}{punto}cuc_calificacionconvencional cc on cc.t_id = ccu.cuc_clfccnndcnstrccion_cuc_calificacionconvencional 
left join {esquema}{punto}cuc_calificartipo cc2 on cc.tipo_calificacion = cc2.t_id
left join {esquema}{punto}cuc_tamanio_baniotipo ctb on ctb.t_id= cc.tamanio_banio
left join {esquema}{punto}cuc_tamanio_cocinatipo ctc on ctc.t_id = cc.tamanio_cocina
)
select *
from cond_4_6
where tipocalificacion ='Residencial'
and (
	calif_banio = 'Baño sin calificacion - Fail'
	or conservacion_banio = 'Baño sin conservacion - Fail'
	or calif_cocina = 'Cocina sin calificacion - Fail'
	or conservacion_cocina = 'Cocina sin conservacion - Fail'
 	)
 	
 