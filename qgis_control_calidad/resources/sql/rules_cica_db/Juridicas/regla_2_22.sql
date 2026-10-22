--regla 2.22
SELECT cdp.numero_predial
,cdp.tipo_persona 
,cdp.tipo_documento 
,cdp.numero_documento 
,cdp.nombre1 || ' '|| cdp.nombre2 ||' '|| cdp.apellido1 ||' '|| cdp.apellido2 as nombres
,cp.coordinador
,cp.usuario as reconocedor
,'Fail' as "2.22"
FROM 
    {esquema}{punto}cica_propietario AS cdp 
    left join {esquema}{punto}cica_predio cp on cdp.numero_predial = cp.numero_predial 
WHERE 
    cdp.tipo_documento IN ('CC', 'CE', 'P', 'TI', 'RC', 'NUIP')
    and 
    (
    cdp.numero_documento !~ '^[0-9]+$'
    or cdp.numero_documento = '0'
    or cdp.numero_documento like '123456789-%'
	or cdp.numero_documento like '987654321-%'
	OR regexp_replace(cdp.numero_documento,'[^0-9]', '', 'g')::NUMERIC = 0)
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')