-- Regla 1.1
WITH tb1 AS (
    SELECT 
        ip.numero_predial_nacional, 
        ic.ilicode AS condicionpredio, 
        substring(ip.numero_predial_nacional, 22, 1) AS pos22, 
        substring(ip.numero_predial_nacional, 23, 8) AS pos23_30
    FROM {esquema}{punto}ilc_predio ip
    LEFT JOIN {esquema}{punto}ilc_condicionprediotipo ic 
        ON ip.condicion_predio = ic.t_id
),
tb_novedades AS (
    SELECT DISTINCT 
        ie.numero_predial,
        ietn.ilicode AS tipo_novedad
    FROM {esquema}{punto}ilc_estructuranovedadnumeropredial ie
    LEFT JOIN {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn
        ON ie.tipo_novedad = ietn.t_id
    WHERE ietn.ilicode IN (
        'Cancelacion',
        'Cambio_Numero_Predial_Mejora_a_Informal',
        'Cambio_Numero_Predial_Mejora_a_NPH'
    )
)
SELECT 
    tb1.*,
    'Fail' AS cond_1_1
FROM tb1
LEFT JOIN tb_novedades tn 
    ON tb1.numero_predial_nacional = tn.numero_predial
WHERE (
    -- Aplicar regla solo si NO cumple la excepción
    NOT (tb1.pos22 = '5' AND tn.numero_predial IS NOT NULL)
)
AND (
    (condicionpredio = 'NPH' AND (pos22 <> '0' OR pos23_30 <> '00000000'))
 OR (condicionpredio = 'Bien_Uso_Publico' AND (pos22 <> '3' OR pos23_30 <> '00000000'))
 OR (condicionpredio = 'Via' AND (pos22 <> '4' OR pos23_30 <> '00000000'))
 OR (condicionpredio IN ('Parque_Cementerio.Unidad_Predial', 'Parque_Cementerio.Matriz') AND (pos22 <> '7' OR pos23_30 <> '00000000'))
 OR (condicionpredio = 'Informal' AND (pos22 <> '2' OR pos23_30 <> '00000000'))
);
