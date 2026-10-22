-- Regla 8.18: Para novedades de Desenglobe: el predio fuente debe existir en R1 y los predios resultado deben ser nuevos.
-- Falla cuando: el fuente no existe en R1 o los resultados no son nuevos.
select ip.numero_predial_nacional npn, 
substring(ip.numero_predial_nacional,18,1)pos_18,
 ietn.ilicode as tipo_novedad,
'Fail' cond_8_18
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where split_part(ietn.ilicode,'_',1) = 'Cambio' and substring(ip.numero_predial_nacional ,18,1) !~ '[A-Z]'
