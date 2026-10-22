-- Regla 8.19: La cantidad de predios fuente en una novedad de englobe debe ser coherente (mínimo 2 fuentes para 1 resultado).
-- Falla cuando: hay menos de 2 predios fuente en un englobe.
select ip.numero_predial_nacional npn, 
ietn.ilicode tiponovedad,
ie.numero_predial np_novedad , 
'Fail' cond_8_19
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode = 'Predio_Nuevo' and ip.numero_predial_nacional <> ie.numero_predial 
