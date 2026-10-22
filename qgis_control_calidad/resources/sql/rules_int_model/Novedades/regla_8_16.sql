-- Regla 8.16: Los predios que aparecen como resultado de una novedad de englobe deben ser predios nuevos (pos18 provisional).
-- Falla cuando: el predio resultante de englobe no tiene codificación provisional en pos18.
select
ip.numero_predial_nacional npn,
ietn.ilicode tiponovedad,
ie.numero_predial np_novedad,
substring(ip.numero_predial_nacional,18,1) pos_18_predio,
substring(ip.numero_predial_nacional,22,1) pos_22_predio,
substring(ie.numero_predial,18,1) pos_18_novedad,
substring(ie.numero_predial,22,1) pos_22_novedad,
r1.numero_predial npn_r1,
case
    when substring(ie.numero_predial,18,1) ~ '^[A-Z9]$' then 'Fail: np_novedad es predio nuevo (pos18 con letra o 9)'
    when substring(ie.numero_predial,22,1) = '2'        then 'Fail: np_novedad es predio informal (pos22=2)'
    when r1.numero_predial is null                       then 'Fail: np_novedad no existe en R1'
end as razon,
'Fail' cond_8_16
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
left join {esquema_r1}{punto}{tabla_r1} r1 on r1.numero_predial = ie.numero_predial
where split_part(ietn.ilicode,'_',1) = 'Cambio'
  and (
    substring(ie.numero_predial,18,1) ~ '^[A-Z9]$'
    or substring(ie.numero_predial,22,1) = '2'
    or r1.numero_predial is null
  )
