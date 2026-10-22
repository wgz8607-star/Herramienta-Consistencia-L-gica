--regla 2.27
SELECT cp.numero_predial
,cpro.tipo_persona 
,cpro.tipo_documento 
,cpro.numero_documento
, cpro.nombre1 
, cpro.nombre2
, cpro.apellido1 
, cpro.apellido2 
, cpro.razon_social
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.27"
FROM {esquema}{punto}cica_predio cp
left JOIN {esquema}{punto}cica_propietario cpro ON cp.numero_predial = cpro.numero_predial 
WHERE cpro.tipo_persona = 'JURIDICA'
and (
	coalesce(regexp_replace(trim(cpro.razon_social), '\s+', ' ', 'g'),'')=''
    or NULLIF(cpro.nombre1,'') is not null
    OR NULLIF(cpro.nombre2,'') is not null
    OR NULLIF(cpro.apellido1,'') is not null
    OR NULLIF(cpro.apellido2,'') is not null
   )
   and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)