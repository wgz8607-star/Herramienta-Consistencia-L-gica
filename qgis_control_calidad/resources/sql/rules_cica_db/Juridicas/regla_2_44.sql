--regla 2.44
SELECT 
    cp.numero_predial, 
    cp.tipo_predio, 
    cp.estado,
    cp.coordinador,
	cp.usuario as reconocedor,
    cp.etapa,
    'Fail' AS cond_2_44
FROM {esquema}{punto}cica_predio cp
WHERE cp.estado = 'ACTIVO' 
  AND (cp.tipo_predio IS NULL OR cp.tipo_predio IN ('P', 'M'))
  AND cp.etapa LIKE ('CONTROL_CALIDAD%');