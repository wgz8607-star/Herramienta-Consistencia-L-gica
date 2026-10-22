--regla 2.25
SELECT cp.numero_predial
, cdp.Tipo_Persona
, cdp.Nombre1
, cdp.Nombre2
, cdp.Apellido1
, cdp.Apellido2
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.25"
FROM {esquema}{punto}cica_propietario AS CDP 
left JOIN {esquema}{punto}cica_predio cp ON cdp.numero_predial  = cp.numero_predial
WHERE cdp.Tipo_Persona = 'JURIDICA'
AND (NULLIF(cdp.Nombre1,'') IS NOT NULL 
OR NULLIF(cdp.Nombre2,'') IS NOT NULL 
OR NULLIF(cdp.Apellido1,'') IS NOT NULL 
OR NULLIF(cdp.Apellido2,'') IS NOT NULL)
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
