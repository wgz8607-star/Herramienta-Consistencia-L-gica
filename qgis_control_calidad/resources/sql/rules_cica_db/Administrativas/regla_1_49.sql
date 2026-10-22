--regla 1.49
SELECT
    cc.numero_predial,
    cc.tipo_documento,
    cc.primer_nombre,
    cc.segundo_nombre,
    cc.primer_apellido,
    cc.segundo_apellido,
    cp.coordinador,
    cp.usuario AS reconocedor,
    'Fail' cond_1_49
FROM {esquema}{punto}cica_contacto cc
INNER JOIN {esquema}{punto}cica_predio cp
    ON cp.numero_predial = cc.numero_predial
WHERE cp.estado = 'ACTIVO'
  AND cp.etapa IN ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
  AND (
        coalesce(cc.primer_nombre,'')
        || coalesce(cc.segundo_nombre,'')
        || coalesce(cc.primer_apellido,'')
        || coalesce(cc.segundo_apellido,'')
        ~ '(LTDA|S\.A\.|& CIA|S\. EN C\.|S\.C\.A\.|S\.A\.S\.)'

        OR
        (
            cc.tipo_documento = 'NIT'
            AND
            coalesce(cc.primer_nombre,'')
            || coalesce(cc.segundo_nombre,'')
            || coalesce(cc.primer_apellido,'')
            || coalesce(cc.segundo_apellido,'') <> ''
        )
      );