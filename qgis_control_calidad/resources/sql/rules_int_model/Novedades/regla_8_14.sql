-- Regla 8.14: Para novedad de Cambio_Numero_Predial_Mejora_a_Informal: el predio resultado debe tener pos22='2' (informal).
-- Falla cuando: el predio destino no tiene codificación informal (pos22 distinto de '2').
select --distinct 
ip.numero_predial_nacional,
ietn.ilicode,
cu.baunit as t_id_baunit,  
ip.t_id as t_id_predio,
'predio cancelado asociado a un terreno'as observacion,
'FAIL' as regla_8_14
from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
left  join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id 
where ietn.ilicode in ('Cancelacion','Cancelacion_por_Englobe','Cancelacion_por_Desenglobe') and cu.ue_cr_terreno is not null
