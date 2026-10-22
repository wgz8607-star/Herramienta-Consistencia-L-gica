--Regla 2.23
SELECT 
    cdp.numero_predial, 
    cdp.tipo_persona, 
    cdp.tipo_documento, 
    cdp.numero_documento, 
    length(cdp.numero_documento) as cant_dig,
    cdp.razon_social,
    cp.coordinador,
    cp.usuario as reconocedor,
    'Fail' as "2.23"
from {esquema}{punto}cica_propietario cdp
left join {esquema}{punto}cica_predio cp on cdp.numero_predial = cp.numero_predial
where (cdp.tipo_documento = 'NIT' and (cdp.numero_documento !~ '^\d{10}$'
    or cdp.numero_documento = '0'
    or cdp.numero_documento like '%123456789%'
	or cdp.numero_documento like '%987654321%')
	and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO'))