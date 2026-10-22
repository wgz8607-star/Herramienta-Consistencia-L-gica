--Regla 4.3
select ip.numero_predial_nacional, cu3.ilicode tipounidad, ct2.ilicode tipologiatipo, 'Fail' cond_4_3
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu ON cu.baunit = ip.t_id 
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu.ue_cr_unidadconstruccion = cu2.t_id 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu2.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}cr_unidadconstrucciontipo cu3 on cu3.t_id = ic.tipo_unidad_construccion 
left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id 
left join {esquema}{punto}cuc_tipologiaconstruccion ct on ct.t_id = ccu.cuc_clfccnndcnstrccion_cuc_tipologiaconstruccion 
left join {esquema}{punto}cuc_tipologiatipo ct2 on ct2.t_id = ct.tipo_tipologia 
where cu3.ilicode = 'Industrial' 
and ct2.ilicode not like 'Industrial.%' 