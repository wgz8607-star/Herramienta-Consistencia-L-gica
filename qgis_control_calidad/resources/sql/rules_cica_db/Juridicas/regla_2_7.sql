-- regla 2.7
SELECT 
 cpd.numero_predial
,cpd.tipo_derecho 
,cp.tipo_predio
,cp.coordinador
,cp.usuario as reconocedor
,'Fail' as "2.7"
FROM {esquema}{punto}cica_predio_derecho cpd
left join {esquema}{punto}cica_predio cp on cpd.numero_predial = cp.numero_predial 
WHERE cpd.tipo_derecho like 'Posesi%' AND cpd.numero_predial IN (
    SELECT numero_predial 
    FROM {esquema}{punto}cica_predio cp
    WHERE cp.tipo_predio <> 'Privado'
)
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')