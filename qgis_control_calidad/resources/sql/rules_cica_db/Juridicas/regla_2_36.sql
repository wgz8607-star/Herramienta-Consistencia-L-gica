--regla 2.36
SELECT 
    cj.numero_predial,
    cj.tipo_documento,
    cj.ente_emisor,
    cj.numero_fuente,
    cj.fecha_documento,
    cp.coordinador,
	cp.usuario as reconocedor,
    'Fail' as "2.36"
FROM 
    {esquema}{punto}cica_justificacion cj 
    left join {esquema}{punto}cica_predio cp on cj.numero_predial = cp.numero_predial 
WHERE 
    ((
        cj.tipo_documento = 'Escritura_Publica' 
        and not LOWER(cj.ente_emisor) LIKE '%notar%'
    )
    OR (
        cj.tipo_documento = 'Sentencia_Judicial' 
        and (not LOWER(cj.ente_emisor) LIKE '%juzgado%'and not LOWER(cj.ente_emisor) LIKE '%tribunal%')
    )
    OR (
        cj.tipo_documento = 'Acto_Administrativo' 
        and (not LOWER(cj.ente_emisor) LIKE '%alcald%'and not LOWER(cj.ente_emisor) LIKE '%ant%'and not LOWER(cj.ente_emisor) LIKE '%incoder%'and not LOWER(cj.ente_emisor) LIKE '%incora%'and not LOWER(cj.ente_emisor) LIKE '%ministerio%')
    ))
  and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')