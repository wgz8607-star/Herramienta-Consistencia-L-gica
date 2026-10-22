--regla 2.28
SELECT cp.numero_predial
,cpro.tipo_persona 
, cpro.numero_documento
, cpro.nombre1 || ' ' || cpro.nombre2 || ' ' || cpro.apellido1 || ' ' || cpro.apellido2 AS nombres
, cpro.razon_social
, cpro.sexo
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.28"
FROM {esquema}{punto}cica_predio cp
LEFT JOIN {esquema}{punto}cica_propietario cpro
    ON cp.numero_predial = cpro.numero_predial
WHERE (
        (cpro.tipo_persona = 'NATURAL' AND (cpro.sexo NOT IN ('Femenino', 'Masculino','Sin_determinar','No_Binario') OR NULLIF(cpro.sexo,'') IS NULL))
        OR
        (cpro.tipo_persona = 'JURIDICA' AND NULLIF(cpro.sexo,'') IS NOT NULL)
      )
     and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)