--regla 2.10
SELECT 
    cp.numero_predial,
    cpro.razon_social,
    cpd.tipo_derecho,
    cp.tipo_predio,
    cp.coordinador,
	cp.usuario as reconocedor,
    'Fail' as "2.10"
FROM 
    {esquema}{punto}cica_predio cp
LEFT JOIN 
    {esquema}{punto}cica_predio_derecho cpd ON cp.numero_predial = cpd.numero_predial 
LEFT JOIN 
    {esquema}{punto}cica_propietario cpro ON cpd.numero_predial = cpro.numero_predial 
WHERE 
    cp.tipo_predio in ('Publico.Baldio','Presunto_Baldio')
    AND cpd.tipo_derecho = 'Dominio'
    AND (
        coalesce(trim(LOWER(razon_social)), '') = ''
        OR NOT (
            LOWER(regexp_replace(trim(razon_social), '\s+', ' ', 'g')) LIKE '%la naci%'
            OR LOWER(regexp_replace(trim(razon_social), '\s+', ' ', 'g')) LIKE 'naci%'
            OR LOWER(regexp_replace(trim(razon_social), '\s+', ' ', 'g')) LIKE '%ant%'
            OR LOWER(regexp_replace(trim(razon_social), '\s+', ' ', 'g')) LIKE '%municipio%'
            OR LOWER(regexp_replace(trim(razon_social), '\s+', ' ', 'g')) LIKE '%agencia nacional de tierras%'
        )
    )
   and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)