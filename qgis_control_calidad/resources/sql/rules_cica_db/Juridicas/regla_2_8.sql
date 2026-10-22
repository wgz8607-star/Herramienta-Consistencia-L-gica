--regla 2.8
SELECT 
cpd.numero_predial
,cpd.tipo_derecho as tipo_derecho
,cp.tipo_predio as tipo_predio
,cp.coordinador
,cp.usuario as reconocedor
, 'Fail' as "2.8"
FROM {esquema}{punto}cica_predio_derecho cpd
left join {esquema}{punto}cica_predio cp on cpd.numero_predial = cp.numero_predial 
WHERE cpd.numero_predial IN (
    SELECT cp.numero_predial 
    FROM {esquema}{punto}cica_predio cp
    WHERE cp.tipo_predio = 'Privado'
) AND cpd.tipo_derecho  like 'Ocupaci%'
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)