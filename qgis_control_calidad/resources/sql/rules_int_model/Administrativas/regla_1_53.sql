 -- Regla 1.53
WITH regla AS (
    SELECT 
        ip.numero_predial_nacional,
        substring(ip.numero_predial_nacional, 6, 2) AS cod_zona,
        substring(ip.numero_predial_nacional, 10, 2) AS cod_comuna,
        substring(ip.numero_predial_nacional, 12, 2) AS cod_barrio,
        substring(ip.numero_predial_nacional, 23, 2) AS cod_torre,
        substring(ip.numero_predial_nacional, 25, 2) AS cod_piso,
        ic.ilicode as condicion,
        'Fail' AS cond_1_53
    FROM {esquema}{punto}ilc_predio ip
    LEFT JOIN {esquema}{punto}ilc_condicionprediotipo ic on ip.condicion_predio = ic.t_id
)
SELECT *
FROM regla
WHERE (cod_zona <> '00'
  AND (cod_comuna = '00' OR cod_barrio = '00'))
  OR (condicion = 'PH.Unidad_Predial'
  AND (cod_torre = '00' OR cod_piso = '00'));
