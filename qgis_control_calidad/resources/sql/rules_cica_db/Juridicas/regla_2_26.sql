--regla 2.26
SELECT  cp.numero_predial
, cdp.Tipo_Persona
, cdp.numero_documento 
, cdp.Nombre1
, cdp.Nombre2
, cdp.apellido1
, cdp.apellido2
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.26"
FROM {esquema}{punto}cica_propietario AS CDP
left JOIN {esquema}{punto}cica_predio cp ON cdp.numero_predial  = cp.numero_predial
WHERE cdp.Tipo_Persona = 'NATURAL'
AND (
    cdp.Nombre1 ILIKE '%SUC%'
    OR cdp.Nombre2 ILIKE '%SUC%'
    OR cdp.apellido1 ILIKE '%SUC%'
    OR cdp.apellido2 ILIKE '%SUC%'
)and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)