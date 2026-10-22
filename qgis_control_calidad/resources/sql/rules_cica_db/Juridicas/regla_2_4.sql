--regla 2.4
SELECT 
  cpd.numero_predial 
, to_timestamp(cpd.fecha_inicio_tenencia, 'MM-DD-YYYY')::date
, current_date "Fecha Actual"
, cc.fecha_visita
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.04"
FROM {esquema}{punto}cica_predio_derecho cpd
left join {esquema}{punto}cica_contacto cc on cpd.numero_predial = cc.numero_predial
left join {esquema}{punto}cica_predio cp on cpd.numero_predial = cp.numero_predial 
WHERE (
	to_timestamp(nullif(cpd.fecha_inicio_tenencia,''), 'MM-DD-YYYY') is null
	or to_timestamp(cpd.fecha_inicio_tenencia, 'MM-DD-YYYY') < '0001-01-01'
	or to_timestamp(cpd.fecha_inicio_tenencia, 'MM-DD-YYYY') > CURRENT_DATE
	OR to_timestamp(nullif(cpd.fecha_inicio_tenencia,''), 'MM-DD-YYYY') > to_timestamp(nullif(cc.fecha_visita ,''), 'MM-DD-YYYY')
)
	and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	