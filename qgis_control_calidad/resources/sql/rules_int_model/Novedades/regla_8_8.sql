-- Regla 8.8: Los predios involucrados en una novedad no pueden tener simultáneamente dos tipos de novedad contradictorios.
-- Falla cuando: un predio tiene novedades incompatibles simultáneamente (ej: englobe y cancelación).
select ip.numero_predial_nacional, 
ietn.ilicode tiponovedad, 
substring(ip.numero_predial_nacional,22,1) pos_22_npn,
substring(ie.numero_predial,22,1) pos_22_novedad,
'Fail' cond_8_8
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode in ('Englobe_Nuevo_FMI','Englobe_Mantiene_FMI') and 
(substring(ip.numero_predial_nacional,22,1)='2' or substring(ie.numero_predial,22,1)='2')
