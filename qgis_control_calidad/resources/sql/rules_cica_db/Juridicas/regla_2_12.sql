--regla 2.12
SELECT cp.numero_predial
, cp.tipo_predio 
, cpd.Tipo_Derecho
, CDP.Razon_social
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.12"
FROM {esquema}{punto}cica_predio cp
INNER JOIN {esquema}{punto}cica_predio_derecho cpd ON cp.numero_predial = cpd.numero_predial
INNER JOIN {esquema}{punto}cica_propietario  CDP ON cp.numero_predial = CDP.numero_predial
WHERE cp.Tipo_Predio in ('Publico.Baldio','Presunto_Baldio')
  AND cpd.Tipo_Derecho like 'Ocupaci%' 
  AND  (regexp_replace(trim(razon_social), '\s+', ' ', 'g') ILIKE '%La Naci%'
    or regexp_replace(trim(razon_social), '\s+', ' ', 'g') ilike 'Naci%'
    OR regexp_replace(trim(razon_social), '\s+', ' ', 'g') ILIKE '%Municipio%'
    OR regexp_replace(trim(razon_social), '\s+', ' ', 'g')  ILIKE '%Agencia Nacional de Tierras%')
   and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)