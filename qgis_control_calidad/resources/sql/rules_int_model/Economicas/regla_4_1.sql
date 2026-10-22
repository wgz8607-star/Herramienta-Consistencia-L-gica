--Regla 4.1
select ip.numero_predial_nacional, cu3.ilicode tipounidad, ct2.ilicode tipologiatipo, 'Fail' cond_4_1
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu ON cu.baunit = ip.t_id 
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu.ue_cr_unidadconstruccion = cu2.t_id 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu2.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}cr_unidadconstrucciontipo cu3 on cu3.t_id = ic.tipo_unidad_construccion 
left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id 
left join {esquema}{punto}cuc_tipologiaconstruccion ct on ct.t_id = ccu.cuc_clfccnndcnstrccion_cuc_tipologiaconstruccion 
left join {esquema}{punto}cuc_tipologiatipo ct2 on ct2.t_id = ct.tipo_tipologia 
where cu3.ilicode = 'Residencial' 
and ct2.ilicode not like 'Residencial.%' 
and ct2.ilicode not in('Conservacion.Residencial_Sencilla_Tipo_1_4014011',
'Conservacion.Residencial_Sencilla_Tipo_2_4024022',
'Conservacion.Residencial_Tipo_3_Restaurada_4024023',
'ED.ED_Multifamiliar_VIP_5_Pisos_9016551',
'ED.ED_Multifamiliar_Vivienda_VIS_Serie_2_Pisos_9011122',
'ED.ED_Multifamiliar_VIS_Hasta_12_Pisos_9016194',
'ED.ED_Multifamiliar_Medio_9026505')