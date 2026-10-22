-- Regla 1.62
WITH regla AS (
    SELECT 
        cp.numero_predial,
        substring(cp.numero_predial, 6, 2) AS cod_zona,
        substring(cp.numero_predial, 10, 2) AS cod_comuna,
        substring(cp.numero_predial, 12, 2) AS cod_barrio,
        substring(cp.numero_predial, 23, 2) AS cod_torre,
        substring(cp.numero_predial, 25, 2) AS cod_piso,
        cp.condicion_predio_tipo as condicion,
        cp.coordinador,
    	cp.usuario as reconocedor,
        'Fail' AS cond_1_62
    FROM {esquema}{punto}cica_predio cp
	WHERE cp.estado = 'ACTIVO'
  	  AND cp.etapa LIKE ('CONTROL_CALIDAD%')
)
SELECT DISTINCT *
FROM regla
WHERE (cod_zona <> '00'
  AND (cod_comuna = '00' OR cod_barrio = '00'))
  OR (condicion = 'PH.Unidad_Predial'
  AND (cod_torre = '00' OR cod_piso = '00'));
