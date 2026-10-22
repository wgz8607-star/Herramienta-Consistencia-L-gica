-- Regla 8.11: El número predial en la novedad debe corresponder a un predio activo en ILC_Predio, no a un predio previamente cancelado.
-- Falla cuando: el NPN corresponde a un predio cancelado.
select ip.numero_predial_nacional,
ietn.ilicode tiponovedad,
substring(ip.numero_predial_nacional,18,1) pos_18_npn,
substring(ip.numero_predial_nacional,22,1) pos_22_npn,
ie.numero_predial np_novedad,
case
    when substring(ip.numero_predial_nacional,18,1) ~ '^[A-Z9]$' then 'Fail: predio que se cancela es predio nuevo (pos18 con letra o 9)'
    when substring(ip.numero_predial_nacional,22,1) = '2'        then 'Fail: predio que se cancela es predio informal (pos22=2)'
end as razon,
'Fail' cond_8_11
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
where ietn.ilicode in ('Cancelacion','Cancelacion_por_Englobe','Cancelacion_por_Desenglobe')
  and (
    substring(ip.numero_predial_nacional,18,1) ~ '^[A-Z9]$'
    or substring(ip.numero_predial_nacional,22,1) = '2'
  )
