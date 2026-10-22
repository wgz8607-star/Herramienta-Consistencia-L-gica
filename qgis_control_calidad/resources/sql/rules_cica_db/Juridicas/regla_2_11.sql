--regla 2.11
SELECT cp.numero_predial
, cp.tipo_predio
, cdp.grupo_etnico
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.11"
FROM {esquema}{punto}cica_predio cp
LEFT JOIN {esquema}{punto}cica_propietario cdp ON cp.numero_predial = cdp.numero_predial
WHERE cp.tipo_predio = 'Territorio_Colectivo' AND (cdp.grupo_etnico = 'Ninguno' or NULLIF(cdp.grupo_etnico,'') is null)
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)