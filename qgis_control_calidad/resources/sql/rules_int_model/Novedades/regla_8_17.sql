-- Regla 8.17: Los predios fuente de una novedad de englobe deben existir en el archivo R1.
-- Falla cuando: un predio fuente de englobe no tiene antecedente registral en R1.
select ip.numero_predial_nacional npn, 
ietn.ilicode tiponovedad,
ie.numero_predial np_novedad , 
re.numero_predial npn_r1,
'Fail' cond_8_17
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
inner join {esquema_r1}.{tabla_r1} re on re.numero_predial = ip.numero_predial_nacional 
where split_part(ietn.ilicode,'_',1) = 'Cambio'
