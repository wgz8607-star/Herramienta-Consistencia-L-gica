-- regla 2.43
SELECT 
    cp.numero_predial,
    cp2.nombre1,
    cp2.nombre2,
    cp2.apellido1,
    cp2.apellido2,
    cp2.razon_social,
    cp2.numero_documento,
    COUNT(
        coalesce(cp2.nombre1,'') ||
        coalesce(cp2.nombre2,'') ||
        coalesce(cp2.apellido1,'') ||
        coalesce(cp2.apellido2,'') ||
        coalesce(cp2.razon_social,'') ||
        coalesce(cp2.numero_documento,'')
    ) AS conteo,
    cp.coordinador,
    cp.usuario as reconocedor,
    'Fail' AS "2.35"
FROM {esquema}{punto}cica_propietario cp2
LEFT JOIN {esquema}{punto}cica_predio cp 
    ON cp2.numero_predial = cp.numero_predial 
WHERE cp.estado = 'ACTIVO'
  AND cp.etapa IN (
        'CONTROL_CALIDAD_GENERAL',
        'CONTROL_CALIDAD_GRUPO'
  )
GROUP BY
    cp.numero_predial,
    cp2.nombre1,
    cp2.nombre2,
    cp2.apellido1,
    cp2.apellido2,
    cp2.razon_social,
    cp2.numero_documento,
    cp2.numero_documento,
    cp.coordinador,
    cp.usuario
HAVING COUNT(
        coalesce(cp2.nombre1,'') ||
        coalesce(cp2.nombre2,'') ||
        coalesce(cp2.apellido1,'') ||
        coalesce(cp2.apellido2,'') ||
        coalesce(cp2.razon_social,'') ||
        coalesce(cp2.numero_documento,'')
    ) > 1;
