--regla 1.61
SELECT DISTINCT
    cp.numero_predial, 
    cp.estado,
    cp.etapa,
    cp.coordinador,
    cp.usuario as reconocedor,
    'Fail' AS cond_1_61
FROM {esquema}{punto}cica_predio cp
WHERE (SUBSTR(cp.numero_predial, 18, 1) = '9' 
       or SUBSTR(cp.numero_predial, 14, 1) = '9')
  AND cp.estado = 'CANCELADO'
  AND cp.etapa LIKE ('CONTROL_CALIDAD%');

