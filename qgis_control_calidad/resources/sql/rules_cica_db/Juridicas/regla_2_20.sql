--regla 2.20
SELECT cdp.numero_predial
,cdp.Tipo_Persona
,cdp.tipo_documento 
,cdp.numero_documento
,cdp.razon_social
,cp.coordinador
,cp.usuario as reconocedor
,'Fail' as "2.20"
FROM {esquema}{punto}cica_propietario AS cdp
left join {esquema}{punto}cica_predio cp on cdp.numero_predial = cp.numero_predial
WHERE cdp.Tipo_Persona = 'JURIDICA'
and (coalesce(regexp_replace(trim( cdp.Tipo_Documento), '\s+', ' ', 'g'),'')=''
or cdp.Tipo_Documento != 'NIT')
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')