-- Regla 8.13: Las novedades de Cancelación solo pueden aplicarse a predios que existen en el archivo R1.
-- Falla cuando: se intenta cancelar un predio nuevo sin antecedente en R1.
select ip.numero_predial_nacional , ietn.ilicode tiponovedad, id.observaciones , 'Fail' cond_8_13
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode in ('Cancelacion') and id.observaciones is null
