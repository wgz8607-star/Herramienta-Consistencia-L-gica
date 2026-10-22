-- regla 2.5
SELECT 
    cp.numero_predial,
    SUBSTRING(cp.numero_predial, 22, 1) AS condicion,
    cpd.tipo_derecho,
    COUNT(*) AS cantidad,
    cp.coordinador,
    cp.usuario AS reconocedor,
    'Fail' AS cond_2_05
FROM {esquema}{punto}cica_predio cp
LEFT JOIN {esquema}{punto}cica_predio_derecho cpd 
    ON cp.numero_predial = cpd.numero_predial
WHERE SUBSTRING(cp.numero_predial, 22, 1) <> '2'
AND cp.numero_predial IN (
    SELECT numero_predial
    FROM {esquema}{punto}cica_predio
    WHERE estado = 'ACTIVO'
    AND etapa IN ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
GROUP BY 
    cp.numero_predial,
    cpd.tipo_derecho,
    cp.coordinador,
    cp.usuario
HAVING COUNT(*) <> 1
AND MAX(cpd.tipo_derecho) = 'Dominio';