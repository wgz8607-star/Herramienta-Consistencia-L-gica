-- Regla 8.nueva_mejoras_englobe: Las mejoras (pos22='5') no deben relacionar novedades de tipo Englobe.
-- Falla cuando: un predio mejora tiene una novedad de englobe asociada.
select
ip.numero_predial_nacional,
substring(ip.numero_predial_nacional,22,1) pos_22_npn,
ie.numero_predial np_novedad,
substring(ie.numero_predial,22,1) pos_22_novedad,
ietn.ilicode tiponovedad,
'Fail' cond_mejoras_englobe
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
where substring(ip.numero_predial_nacional,22,1) = '5'
  and ietn.ilicode like 'Englobe%'
