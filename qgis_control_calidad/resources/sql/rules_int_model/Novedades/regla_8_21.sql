-- Regla 8.21: Para novedad de Cancelación_por_Englobe: el predio cancelado debe aparecer como fuente en la respectiva novedad de englobe.
-- Falla cuando: el predio cancelado no está como fuente en el englobe correspondiente.
SELECT ip.numero_predial_nacional,
re.numero_predial np_r1,
ietn.ilicode tiponovedad,
'Fail' cond_8_21
from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
LEFT JOIN {esquema_r1}.{tabla_r1} re ON re.numero_predial = ip.numero_predial_nacional
WHERE ietn.ilicode= 'Predio_Nuevo'
and (coalesce(re.numero_predial,'') = ie.numero_predial
OR coalesce(re.numero_predial,'') = ip.numero_predial_nacional)
