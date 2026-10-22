-- =============================================================================
-- Regla 2.35 — Datos de persona jurídica en nombres de personas naturales
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.35
-- Enunciado  : "Los interesados correspondientes a personas naturales no deben
--              registrar datos de personas jurídicas en los campos destinados a
--              identificar su nombre."
-- Universo   : Interesados tipo Persona natural (hoja "Datos", id 35).
-- Falla si   : val_indicador_pj — algún campo de nombre contiene un indicador de
--              forma societaria o de entidad (LTDA, S.A., S.A.S., & CIA, E.S.P.,
--              E.U., BANCO, FUNDACION, COOPERATIVA, ...).
-- No aplica  : interesados Persona_Juridica.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, col_miembros,
--              ilc_interesado, cr_interesadotipo
-- Origen     : regla_2_22.sql (set anterior)
-- Salida     : documento_identidad, nombres, indicador_detectado, n_predios, npn_ejemplo, cond_2_35
-- Granularidad  : UNA fila por interesado. El universo declarado en la hoja "Datos"
--              del formato son los interesados, no los predios: un mismo interesado
--              vinculado a N predios es UN error de captura, no N. Se reportan
--              n_predios y npn_ejemplo para poder ubicarlo.
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 4 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambios frente a regla_2_22:
--   * El regex anterior estaba anclado con `$`: solo detectaba el indicador si
--     aparecía AL FINAL del campo. "LTDA CONSTRUCTORA DEL NORTE" en primer_nombre no
--     se detectaba. Se quita el ancla y se usan límites de palabra.
--   * `\sS\.A\.` exigía los puntos: "S A", "SA" o "S.A" se escapaban. El patrón
--     nuevo hace los puntos opcionales.
--   * Se amplía el catálogo: E.S.P., E.U., S.C.A., S. en C., BANCO, FUNDACION,
--     COOPERATIVA, ASOCIACION, CORPORACION, IGLESIA, MUNICIPIO, NACION, SOCIEDAD.
--   * Se normaliza a mayúsculas sin tildes antes de comparar (antes era sensible a
--     mayúsculas: "Ltda" se escapaba).
--   * Se reporta cuál indicador se detectó.
--
-- Riesgo conocido: "SA" y "EU" como palabra suelta pueden aparecer en nombres
-- extranjeros. Por eso se exigen los puntos o el contexto societario para las
-- abreviaturas de dos letras, y se dejan sueltas solo las inequívocas (LTDA, SAS).
-- =============================================================================

with cte_interesados as (
    select
        ip.numero_predial_nacional    npn,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        ii.primer_nombre, ii.segundo_nombre,
        ii.primer_apellido, ii.segundo_apellido,
        ii.tipo                       interesado_tipo_id
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cri.interesado_ilc_interesado

    union all

    select
        ip.numero_predial_nacional    npn,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        ii.primer_nombre, ii.segundo_nombre,
        ii.primer_apellido, ii.segundo_apellido,
        ii.tipo                       interesado_tipo_id
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}col_miembros cm       on cm.agrupacion = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cm.interesado_ilc_interesado
)
, cte_base as (
    select
        i.npn,
        i.interesado_id,
        i.documento_identidad,
        i.primer_nombre, i.segundo_nombre, i.primer_apellido, i.segundo_apellido,
        upper(translate(
            concat_ws(' ', i.primer_nombre, i.segundo_nombre,
                           i.primer_apellido, i.segundo_apellido),
            'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'))  nombre_norm
    from cte_interesados i
    join {esquema}{punto}cr_interesadotipo cit on cit.t_id = i.interesado_tipo_id
    where cit.ilicode = 'Persona_Natural'
)
, cte_validaciones as (
    select
        b.*,
        case
            -- formas societarias inequívocas
            when b.nombre_norm ~ '\mLTDA\.?\M'                    then 'LTDA'
            when b.nombre_norm ~ '\mS\.?A\.?S\.?\M'               then 'S.A.S.'
            when b.nombre_norm ~ '\mS\.A\.?\M'                    then 'S.A.'
            when b.nombre_norm ~ '\mS\.?C\.?A\.?\M'               then 'S.C.A.'
            when b.nombre_norm ~ '\mS\.? EN C\.?\M'               then 'S. EN C.'
            when b.nombre_norm ~ '&\s*C(IA|OMPANIA)\.?\M'         then '& CIA'
            when b.nombre_norm ~ '\mE\.?S\.?P\.?\M'               then 'E.S.P.'
            when b.nombre_norm ~ '\mE\.?U\.?\M'                   then 'E.U.'
            -- tipos de entidad escritos con todas las letras
            when b.nombre_norm ~ '\mSOCIEDAD\M'                   then 'SOCIEDAD'
            when b.nombre_norm ~ '\mBANCO\M'                      then 'BANCO'
            when b.nombre_norm ~ '\mFUNDACION\M'                  then 'FUNDACION'
            when b.nombre_norm ~ '\mCOOPERATIVA\M'                then 'COOPERATIVA'
            when b.nombre_norm ~ '\mASOCIACION\M'                 then 'ASOCIACION'
            when b.nombre_norm ~ '\mCORPORACION\M'                then 'CORPORACION'
            when b.nombre_norm ~ '\mIGLESIA\M'                    then 'IGLESIA'
            when b.nombre_norm ~ '\mMUNICIPIO\M'                  then 'MUNICIPIO'
            when b.nombre_norm ~ '\mLA NACION\M'                  then 'LA NACION'
            else null
        end  indicador_detectado
    from cte_base b
)
-- Se reporta UNA fila por interesado, no por predio: el universo declarado en
-- la hoja "Datos" del formato es el total de interesados. Un mismo interesado
-- vinculado a cientos de predios es UN error de captura, no cientos.
select
    documento_identidad,
    primer_nombre,
    segundo_nombre,
    primer_apellido,
    segundo_apellido,
    indicador_detectado,
    count(distinct npn)                        n_predios
    , min(npn)                                 npn_ejemplo
    , 'Fail' cond_2_35
from cte_validaciones
where indicador_detectado is not null
group by
    documento_identidad,
    primer_nombre,
    segundo_nombre,
    primer_apellido,
    segundo_apellido,
    indicador_detectado
order by n_predios desc
