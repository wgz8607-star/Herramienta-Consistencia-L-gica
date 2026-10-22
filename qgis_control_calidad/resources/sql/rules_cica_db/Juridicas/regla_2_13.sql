--regla 2.13
SELECT cp.numero_predial
, cp.tipo_predio 
, cpd.Tipo_Derecho
, CDP.Tipo_Persona
, cdp.tipo_documento 
, cdp.numero_documento
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.13"
FROM {esquema}{punto}cica_predio cp
inner JOIN {esquema}{punto}cica_predio_derecho AS CPD ON cp.numero_predial = CPD.numero_predial
inner JOIN {esquema}{punto}cica_propietario AS CDP ON cp.numero_predial = CDP.numero_predial
WHERE cp.Tipo_Predio in ('Publico.Baldio','Presunto_Baldio','Publico.Fiscal', 'Publico.Uso_Publico','Publico.Patrimonial') 
AND cpd.Tipo_Derecho = 'Dominio' 
AND CDP.Tipo_Persona != 'JURIDICA'
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)