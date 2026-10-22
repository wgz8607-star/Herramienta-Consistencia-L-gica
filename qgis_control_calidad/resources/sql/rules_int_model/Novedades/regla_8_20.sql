-- Regla 8.20: Los predios con novedad de tipo Predio_Nuevo no deben existir en el archivo R1.
-- Falla cuando: un predio marcado como nuevo ya tiene antecedente registral en R1.
select ip.numero_predial_nacional npn, 
substring(ip.numero_predial_nacional ,18,1) pos18_npn,
ietn.ilicode tiponovedad,
ie.numero_predial np_novedad ,
substring(ie.numero_predial  ,18,1) pos18_novedad,
'Fail' cond_8_20
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode = 'Predio_Nuevo' 
and (substring(ip.numero_predial_nacional ,18,1) !~ '[A-Z]' 
	or substring(ie.numero_predial  ,18,1)!~ '[A-Z]')
