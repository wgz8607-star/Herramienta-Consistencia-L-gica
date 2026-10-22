-- Regla 8.6: Para novedad de Desenglobe simple: el predio fuente debe quedar con novedad de cancelación y los predios resultantes deben ser nuevos.
-- Falla cuando: el predio fuente no se cancela o los resultantes no son nuevos.
select ip.numero_predial_nacional , ietn.ilicode tiponovedad, ip.matricula_inmobiliaria , 'Fail' cond_8_6
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode in ('Englobe_Nuevo_FMI','Englobe_Mantiene_FMI') and (ip.matricula_inmobiliaria is null or ip.matricula_inmobiliaria = '0')
