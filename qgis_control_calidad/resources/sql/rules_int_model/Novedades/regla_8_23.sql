-- Regla 8.23: Los predios con novedad deben tener la fecha de la novedad diligenciada.
-- Falla cuando: la fecha está nula o es inválida.
select re.numero_predial np_r1,
ip.numero_predial_nacional npn_predio,
ie.numero_predial npn_novedad,
'Fail' cond_8_23
from {esquema_r1}.{tabla_r1} re
left join {esquema}{punto}ilc_predio ip on ip.numero_predial_nacional = re.numero_predial
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.numero_predial = re.numero_predial
where ip.numero_predial_nacional is null and ie.numero_predial is null
