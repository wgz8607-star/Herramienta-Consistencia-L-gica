--regla 2.6
SELECT 
cpd.numero_predial
,cpd.tipo_derecho
,cp.tipo_predio 
,cp.matricula 
,cp.coordinador
,cp.usuario as reconocedor
, 'Fail' as "2.06"
FROM {esquema}{punto}cica_predio_derecho cpd
inner join {esquema}{punto}cica_predio cp on cpd.numero_predial = cp.numero_predial 
WHERE (cpd.tipo_derecho = 'Dominio' AND cpd. numero_predial IN (
    SELECT cp.numero_predial 
    FROM {esquema}{punto}cica_predio cp
    WHERE cp.tipo_predio = 'Privado' AND (NULLIF(cp.matricula,'') IS NULL OR cp.matricula= '' or cp.matricula::numeric = 0)
))
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)