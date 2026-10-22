--regla 2.17
SELECT cp.numero_predial
,LENGTH(cp.matricula) as "Longitud"
,cp.matricula, cp.tiene_fmi
, cp.coordinador
, cp.usuario as reconocedor
,'Fail' as "2.17"
FROM {esquema}{punto}cica_predio cp
WHERE LENGTH(cp.matricula) > 7 
AND CP.Tiene_FMI != 'NO'
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)