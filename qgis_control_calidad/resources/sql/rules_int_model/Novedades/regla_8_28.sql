-- Regla 8.28: Todo número predial con codificación provisional (pos18 = letra o '9') debe estar asociado al menos a un registro de novedad.
-- Falla cuando: un predio con NPN provisional no tiene novedades registradas.
select
ip.numero_predial_nacional,
substring(ip.numero_predial_nacional,18,1) pos_18,
'Fail' cond_8_28
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
where substring(ip.numero_predial_nacional,18,1) ~ '^[A-Z9]$'
  and ie.numero_predial is null
