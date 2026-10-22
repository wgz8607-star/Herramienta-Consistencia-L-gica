-- Regla 8.27: Todas las mejoras registradas en R1 deben tener asociada una novedad de 'Cambio_Numero_Predial' o 'Cancelación'.
-- Falla cuando: una mejora en R1 no tiene novedad que justifique su transformación.
WITH mejoras AS (
  SELECT re.numero_predial, '5' condicion
  FROM {esquema_r1}{punto}{tabla_r1} re
  WHERE substring(re.numero_predial,22,1) = '5'
),
nov_mej AS (
  SELECT
    ie.numero_predial AS npn_mejora,
    iet.ilicode tipo_novedad,
    ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales AS soporte_id
  FROM {esquema}{punto}ilc_estructuranovedadnumeropredial ie
  left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad iet on ie.tipo_novedad=iet.t_id
  WHERE substring(ie.numero_predial,22,1) = '5'
)
SELECT
  m.numero_predial AS npn_mejora_r1,
  m.condicion,
  nm.tipo_novedad,
  nm.npn_mejora,
  ip.numero_predial_nacional,
  CASE
    WHEN nm.npn_mejora IS NULL THEN 'Fail: sin novedad'
    WHEN nm.tipo_novedad !~ 'Cambio_Numero_Predial_Mejora_a_Informal|Cambio_Numero_Predial_Mejora_a_NPH|Cancelacion' THEN 'Fail: tipo_novedad no válido'
    WHEN nm.tipo_novedad IN ('Cambio_Numero_Predial_Mejora_a_Informal','Cambio_Numero_Predial_Mejora_a_NPH') AND ip.numero_predial_nacional IS null THEN 'Fail: La mejora no relaciona numero predial en ilc_predio'
    WHEN nm.tipo_novedad = 'Cancelacion' and nm.npn_mejora <> ip.numero_predial_nacional THEN 'Fail: La cancelacion no relaciona el mismo numero_predial'
    ELSE 'OK'
  END AS estado,
  count(*) over (partition by m.numero_predial) total_mejoras_r1,
  count(*) filter (where nm.tipo_novedad like 'Cambio%') over (partition by m.numero_predial) total_cambios,
  count(*) filter (where nm.tipo_novedad = 'Cancelacion') over (partition by m.numero_predial) total_cancelaciones,
  count(*) filter (where nm.npn_mejora is null) over (partition by m.numero_predial) total_sin_novedad
FROM mejoras m
LEFT JOIN nov_mej nm ON nm.npn_mejora = m.numero_predial
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.t_id = nm.soporte_id
LEFT JOIN {esquema}{punto}ilc_predio ip on id.ilc_predio = ip.t_id
ORDER BY estado, npn_mejora_r1
