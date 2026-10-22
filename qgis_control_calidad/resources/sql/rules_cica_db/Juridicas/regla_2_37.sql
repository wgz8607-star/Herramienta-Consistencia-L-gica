--regla 2.37
SELECT 
	cpro.numero_predial
    , cpro.departamento
    , cpro.municipio
    , cp.coordinador
	, cp.usuario as reconocedor
    , 'Fail' as "2.37"
FROM {esquema}{punto}cica_propietario cpro
left join {esquema}{punto}cica_predio cp on cpro.numero_predial = cp.numero_predial
WHERE (coalesce(regexp_replace(trim(cpro.departamento), '\s+', ' ', 'g'),'')=''
  or coalesce(regexp_replace(trim(cpro.municipio), '\s+', ' ', 'g'),'')='')
  and cpro.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
ORDER BY cpro.numero_predial