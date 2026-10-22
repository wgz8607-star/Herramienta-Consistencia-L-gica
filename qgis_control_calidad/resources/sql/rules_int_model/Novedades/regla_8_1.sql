-- Regla 8.1: Todo número predial en ILC_EstructuraNovedadNumeroPredial debe tener exactamente 30 dígitos.
-- Falla cuando: la longitud del NPN es diferente a 30 caracteres.
select ip.numero_predial_nacional , ietn.ilicode tiponovedad, ip.matricula_inmobiliaria , 'Fail' cond_8_1
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode in ('Desenglobe_Division_Material','Desenglobe_Venta_Parcial') and (ip.matricula_inmobiliaria is null or ip.matricula_inmobiliaria = '0')
