-- Regla 8.7: Los predios con novedad de Cambio de Número Predial deben tener exactamente un predio origen y un predio destino; el predio origen debe quedar cancelado.
-- Falla cuando: hay más de un origen/destino o el origen no queda cancelado.
with cond_8_7 AS(
select ip.numero_predial_nacional,
ietn.ilicode tiponovedad,
ie.numero_predial np_novedad,
rdcr.numero_predial npn_r1,
'Fail' cond_8_7
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
left join {esquema_r1}{punto}{tabla_r1} rdcr on rdcr.numero_predial = ie.numero_predial
)
SELECT * FROM cond_8_7
WHERE cond_8_7.npn_r1 is null
AND cond_8_7.tiponovedad IN ('Englobe_Nuevo_FMI','Englobe_Mantiene_FMI')
