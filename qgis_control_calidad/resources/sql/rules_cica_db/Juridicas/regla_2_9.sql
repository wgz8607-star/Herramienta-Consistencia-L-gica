--regla 2.9
SELECT cp.numero_predial 
, cp.matricula 
, cp.tipo_predio
, cpd.tipo_derecho
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.09"
FROM {esquema}{punto}cica_predio_derecho cpd
left JOIN {esquema}{punto}cica_predio cp ON cpd.numero_predial  = cp.numero_predial 
WHERE cp.tipo_predio in ('Publico.Patrimonial', 'Publico.Fiscal', 'Publico.Baldio', 'Publico.Uso_Publico','Presunto_Baldio')
AND cpd.tipo_derecho like 'Posesi%'
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)