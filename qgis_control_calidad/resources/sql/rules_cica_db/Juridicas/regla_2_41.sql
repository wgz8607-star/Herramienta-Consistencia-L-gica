--regla 2.41
SELECT cp.numero_predial
	,cp.condicion_predio_tipo
	,cp.tipo_informalidad
	,cpd.tipo_derecho
	,cp.coordinador
	,cp.usuario as reconocedor
     , 'Fail' as "2.41"
FROM {esquema}{punto}cica_predio cp
LEFT JOIN {esquema}{punto}cica_predio_derecho cpd
    ON cp.numero_predial = cpd.numero_predial
WHERE cp.condicion_predio_tipo = 'Informal'
  AND (
        cp.tipo_informalidad <> cpd.tipo_derecho
        OR cpd.tipo_derecho = 'Dominio'
      )
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')