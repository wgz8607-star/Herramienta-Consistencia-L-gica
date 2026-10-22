--regla 2.38
SELECT 
	cp.numero_predial
	,cp.estado 
	,cpro.tipo_persona 
	,cpro.numero_documento 
	,cpro.estado
	,cp.coordinador
	,cp.usuario as reconocedor
	,'Fail' as "2.38"
FROM {esquema}{punto}cica_predio cp
LEFT JOIN {esquema}{punto}cica_propietario cpro ON cp.numero_predial = cpro.numero_predial
WHERE coalesce(regexp_replace(trim(cpro.numero_predial), '\s+', ' ', 'g'),'')=''
AND cp.estado <> 'CANCELADO'
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	and substring(cp.numero_predial, 22, 9) not in ('900000000', '800000000')
)