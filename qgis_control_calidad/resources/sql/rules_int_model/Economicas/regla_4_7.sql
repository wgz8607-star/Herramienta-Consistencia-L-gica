
 	--regla 4.7 	

with cond_4_7 as(
select ip.numero_predial_nacional
, cc2.ilicode tipocalificacion, 
ctb.ilicode  tamanio_banio,
ceb.ilicode enchape_banio,
cmb.ilicode mobiliario_banio,
cbanio.ilicode conservacion_banio,
ctc.ilicode tamanio_cocina,
cec.ilicode enchape_cocina,
cmc.ilicode mobiliario_cocina,
ccocina.ilicode conservacion_cocina,
'Fail' cond_4_7
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu ON cu.baunit = ip.t_id 
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu.ue_cr_unidadconstruccion = cu2.t_id 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu2.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id 
inner join {esquema}{punto}cuc_calificacionconvencional cc on cc.t_id = ccu.cuc_clfccnndcnstrccion_cuc_calificacionconvencional 
left join {esquema}{punto}cuc_calificartipo cc2 on cc.tipo_calificacion = cc2.t_id 	
left join {esquema}{punto}cuc_tamanio_baniotipo ctb on ctb.t_id= cc.tamanio_banio
left join {esquema}{punto}cuc_tamanio_cocinatipo ctc on ctc.t_id = cc.tamanio_cocina
left join {esquema}{punto}cuc_enchape_baniotipo ceb on ceb.t_id = cc.enchape_banio
left join {esquema}{punto}cuc_enchape_cocinatipo cec on cec.t_id = cc.enchape_cocina
left join {esquema}{punto}cuc_mobiliario_baniotipo cmb on cmb.t_id = cc.mobiliario_banio
left join {esquema}{punto}cuc_mobiliario_cocinatipo cmc on cmc.t_id = cc.mobiliario_cocina
left join {esquema}{punto}cuc_estadoconservaciontipo cbanio on cbanio.t_id = cc.conservacion_banio
left join {esquema}{punto}cuc_estadoconservaciontipo ccocina on ccocina.t_id = cc.conservacion_cocina
where cc2.ilicode ='Comercial'
)
select * 
from cond_4_7 
where 
enchape_banio is not null or 
conservacion_banio is not null or 
enchape_cocina is not null or 
conservacion_cocina is not null