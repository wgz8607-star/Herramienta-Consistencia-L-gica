--Regla 1.17
WITH predios_base AS (
    SELECT 
        ip.numero_predial_nacional,
        id.ilicode AS destinacioneconomica,
        substring(ip.numero_predial_nacional, 22, 1) AS pos22,
        ip.t_id AS predio_id
    FROM {esquema}{punto}ilc_predio ip
    LEFT JOIN {esquema}{punto}ilc_destinacioneconomicatipo id 
        ON id.t_id = ip.destinacion_economica
),
unidades_construccion AS (
    SELECT 
        cu.baunit AS predio_id,
        COUNT(cu2.t_id) AS unidades_construccion
    FROM {esquema}{punto}col_uebaunit cu
    LEFT JOIN {esquema}{punto}cr_unidadconstruccion cu2 
        ON cu2.t_id = cu.ue_cr_unidadconstruccion
    GROUP BY cu.baunit
),
novedades_excepcion AS (
    SELECT DISTINCT 
        ie.numero_predial
    FROM {esquema}{punto}ilc_estructuranovedadnumeropredial ie
    LEFT JOIN {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn
        ON ietn.t_id = ie.tipo_novedad
    WHERE ietn.ilicode IN (
        'Cancelacion',
        'Cambio_Numero_Predial_Mejora_a_Informal',
        'Cambio_Numero_Predial_Mejora_a_NPH'
    )
)
SELECT 
    pb.numero_predial_nacional,
    pb.destinacioneconomica,
    COALESCE(uc.unidades_construccion, 0) AS unidadesconstruccion,
    'Fail' AS cond_1_17
FROM predios_base pb
LEFT JOIN unidades_construccion uc 
    ON pb.predio_id = uc.predio_id
LEFT JOIN novedades_excepcion ne 
    ON pb.numero_predial_nacional = ne.numero_predial
WHERE pb.destinacioneconomica IN (
        'Comercial', 
        'Educativo', 
        'Habitacional', 
        'Industrial', 
        'Salubridad', 
        'Institucional'
    )
  AND COALESCE(uc.unidades_construccion, 0) < 1
  AND NOT (pb.pos22 = '5' AND ne.numero_predial IS NOT NULL);
 