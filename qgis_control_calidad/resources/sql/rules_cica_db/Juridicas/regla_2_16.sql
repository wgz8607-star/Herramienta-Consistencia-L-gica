--regla 2.16
with regla as (
SELECT cp.numero_predial
,cpd.Tipo_Derecho
,cp.Matricula
,max(to_timestamp(cpd.Fecha_Inicio_Tenencia,'MM-DD-YYYY')::date) over (partition by cp.numero_predial) Fecha_Inicio_Tenencia
,max(to_timestamp(j.fecha_documento,'MM-DD-YYYY')::date) over (partition by cp.numero_predial) fecha_documento 
, cp.coordinador
, cp.usuario as reconocedor
,'Fail' as "2.16"
FROM {esquema}{punto}cica_predio cp
inner JOIN {esquema}{punto}cica_predio_derecho AS CPD ON cp.numero_predial = CPD.numero_predial
inner join {esquema}{punto}cica_justificacion  j on cp.numero_predial = j.numero_predial 
WHERE (nullif(cp.Matricula,'') IS NOT NULL AND cp.Matricula <> '0') 
AND cpd.Tipo_Derecho = 'Dominio' 
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
)
select distinct * 
from regla 
where regla.fecha_inicio_tenencia < regla.fecha_documento