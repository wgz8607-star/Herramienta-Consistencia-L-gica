--regla 2.1
SELECT 
    cp.numero_predial,
    cp.matricula,
    LENGTH(cp.matricula) as "Longitud"
    ,cp.tenencia
    ,cp.coordinador
	,cp.usuario as reconocedor
    ,'Fail' as "2.01"
FROM 
    {esquema}{punto}cica_predio cp
WHERE 
    cp.cancela_inscribe <> 'C'
    AND nullif(cp.matricula,'') IS NOT NULL
    AND cp.matricula <> '0'
    AND (
        NOT cp.matricula ~ '^[0-9]+$'
        OR LENGTH(cp.matricula) < 1 
        OR LENGTH(cp.matricula) > 8  
        OR cp.matricula::NUMERIC = 0
    )
and numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)