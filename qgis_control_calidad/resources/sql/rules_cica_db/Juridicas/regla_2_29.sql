--regla 2.29
SELECT cp.numero_predial
,cpro.numero_documento
,cpro.nombre1 
,cpro.nombre2 
,cpro.apellido1 
,cpro.apellido2
,cp.coordinador
,cp.usuario as reconocedor
, 'Fail' as "2.29"
FROM {esquema}{punto}cica_predio cp
left JOIN {esquema}{punto}cica_propietario cpro ON cp.numero_predial = cpro.numero_predial
WHERE cpro.tipo_persona = 'NATURAL'
AND (
cpro.nombre1 ilike '%LTDA%' or cpro.nombre1 ilike '%& CIA%' or cpro.nombre1 ilike '%S. EN C%' or cpro.nombre1 ilike '%S.C.A%' or cpro.nombre1 ilike '%S.A.S%'
or cpro.nombre2 ilike '%LTDA%' or cpro.nombre2 ilike '%& CIA%' or cpro.nombre2 ilike '%S. EN C%' or cpro.nombre2 ilike '%S.C.A%' or cpro.nombre2 ilike '%S.A.S%'
or cpro.apellido1 ilike '%LTDA%' or cpro.apellido1 ilike '%& CIA%' or cpro.apellido1 ilike '%S. EN C%' or cpro.apellido1 ilike '%S.C.A%' or cpro.apellido1 ilike '%S.A.S%'
or cpro.apellido2 ilike '%LTDA%' or cpro.apellido2 ilike '%& CIA%' or cpro.apellido2 ilike '%S. EN C%' or cpro.apellido2 ilike '%S.C.A%' or cpro.apellido2 ilike '%S.A.S%'
)
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
