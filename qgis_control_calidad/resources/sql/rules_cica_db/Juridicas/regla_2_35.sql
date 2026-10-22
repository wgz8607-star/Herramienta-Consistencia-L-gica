--regla 2.35
WITH cond_2_35 AS (
select 
	cj.numero_predial,
    cj.tipo_documento,
    cj.ente_emisor,
    cj.numero_fuente,
    cj.fecha_documento
    , 'Fail' as "2.35"
from 
    {esquema}{punto}cica_justificacion cj 
where 
    tipo_documento in ('Escritura_Publica', 'Sentencia_Judicial', 'Acto_Administrativo')
    and (
        coalesce(regexp_replace(trim(cj.ente_emisor), '\s+', ' ', 'g'),'') LIKE ''
        or coalesce(regexp_replace(trim(cj.numero_fuente), '\s+', ' ', 'g'),'') LIKE ''
        or coalesce(regexp_replace(trim(cj.fecha_documento), '\s+', ' ', 'g'),'') LIKE ''
    )
UNION ALL
SELECT 
    cj.numero_predial,
    cj.tipo_documento,
    cj.ente_emisor,
    cj.numero_fuente,
    cj.fecha_documento
    , 'Fail' as "2.35"
FROM 
    {esquema}{punto}cica_justificacion cj 
WHERE 
    cj.tipo_documento = 'Documento_Privado'
    AND (
        coalesce(regexp_replace(trim(cj.fecha_documento), '\s+', ' ', 'g'),'') LIKE ''
        OR not coalesce(regexp_replace(trim(cj.ente_emisor), '\s+', ' ', 'g'),'') LIKE ''
        OR not coalesce(regexp_replace(trim(cj.numero_fuente), '\s+', ' ', 'g'),'') LIKE ''
    )
UNION ALL
SELECT 
    cj.numero_predial,
    cj.tipo_documento,
    cj.ente_emisor,
    cj.numero_fuente,
    cj.fecha_documento,
    'Fail' as "regla_2_35"
FROM {esquema}{punto}cica_justificacion cj 
WHERE 
    cj.tipo_documento = 'Sin_Documento' 
    OR coalesce(regexp_replace(trim(cj.tipo_documento), '\s+', ' ', 'g'),'') LIKE ''
    AND NOT (
        coalesce(regexp_replace(trim(cj.ente_emisor), '\s+', ' ', 'g'),'') LIKE ''
        AND coalesce(regexp_replace(trim(cj.numero_fuente), '\s+', ' ', 'g'),'') LIKE ''
        AND coalesce(regexp_replace(trim(cj.fecha_documento), '\s+', ' ', 'g'),'') LIKE ''
    ))
    SELECT cond_2_35.*,
    cp.coordinador,
	cp.usuario as reconocedor
    FROM cond_2_35
    left join {esquema}{punto}cica_predio cp on cond_2_35.numero_predial = cp.numero_predial
    WHERE cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')