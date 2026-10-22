--regla 2.21
SELECT cdp.numero_predial
, cdp.Tipo_Persona
, cdp.tipo_documento 
,cdp.numero_documento 
, cdp.nombre1 || ' '|| cdp.nombre2 ||' '|| cdp.apellido1 ||' '|| cdp.apellido2 as nombres
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.21"
FROM {esquema}{punto}cica_propietario AS cdp 
left join {esquema}{punto}cica_predio cp on cdp.numero_predial = cp.numero_predial
WHERE cdp.Tipo_Persona = 'NATURAL' AND cdp.Tipo_Documento NOT IN ('CC', 'CE', 'P', 'TI', 'RC')
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')