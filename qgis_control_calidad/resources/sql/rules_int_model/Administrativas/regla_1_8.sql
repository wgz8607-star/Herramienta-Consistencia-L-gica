--Regla 1.8
SELECT 
    ip.numero_predial_nacional, 
    SUBSTRING(ip.numero_predial_nacional, 22, 1) AS pos_22,
    ietn.ilicode AS tipo_novedad, 
    'Fail' AS cond_1_8
FROM {esquema}{punto}ilc_predio ip 
LEFT JOIN {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id 
    ON id.ilc_predio = ip.t_id 
LEFT JOIN {esquema}{punto}ilc_estructuranovedadnumeropredial ie 
    ON ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
LEFT JOIN {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn 
    ON ietn.t_id = ie.tipo_novedad
WHERE SUBSTRING(ip.numero_predial_nacional, 22, 1) IN ('1','6')
UNION
SELECT 
    ip.numero_predial_nacional, 
    SUBSTRING(ip.numero_predial_nacional, 22, 1) AS pos_22,
    ietn.ilicode AS tipo_novedad, 
    'Fail' AS cond_1_8
FROM {esquema}{punto}ilc_predio ip 
LEFT JOIN {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id 
    ON id.ilc_predio = ip.t_id 
LEFT JOIN {esquema}{punto}ilc_estructuranovedadnumeropredial ie 
    ON ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
LEFT JOIN {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn 
    ON ietn.t_id = ie.tipo_novedad
WHERE SUBSTRING(ip.numero_predial_nacional, 22, 1) = '5' 
  AND ietn.ilicode NOT IN (
        'Cancelacion', 'Cambio_Numero_Predial_Mejora_a_Informal', 'Cambio_Numero_Predial_Mejora_a_NPH');
