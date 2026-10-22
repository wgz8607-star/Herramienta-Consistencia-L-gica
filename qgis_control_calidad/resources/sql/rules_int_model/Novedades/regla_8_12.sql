-- Regla 8.12: Para novedades de tipo Englobe: el número predial resultado debe tener pos22 igual al pos22 del predio fuente.
-- Falla cuando: hay cambio de condición predial (pos22) en el englobe.
select ip.numero_predial_nacional , ietn.ilicode tiponovedad, ie.numero_predial np_novedad , 'Fail' cond_8_12
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode in ('Cancelacion','Cancelacion_por_Englobe','Cancelacion_por_Desenglobe') 
and ip.numero_predial_nacional <> ie.numero_predial 
