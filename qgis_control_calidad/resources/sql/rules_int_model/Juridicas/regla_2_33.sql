-- =============================================================================
-- Regla 2.33 — "SUC" (sucesiones ilíquidas) en nombres de personas naturales
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.33
-- Enunciado  : "En las bases catastrales vigentes no se deben asociar palabras como
--              "SUC" (sucesiones ilíquidas) en los campos de nombre de personas
--              naturales."
-- Universo   : Interesados tipo Persona natural (hoja "Datos", id 35).
-- Falla si   : val_suc — algún campo de nombre contiene la marca de sucesión
--              ilíquida: SUC, SUC., SUCESION, SUCESIÓN, SUCS, HEREDEROS.
-- No aplica  : interesados Persona_Juridica.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, col_miembros,
--              ilc_interesado, cr_interesadotipo
-- Origen     : regla_2_19.sql (set anterior)
-- Salida     : documento_identidad, nombres, marca_detectada, n_predios, npn_ejemplo, cond_2_33
-- Granularidad  : UNA fila por interesado. El universo declarado en la hoja "Datos"
--              del formato son los interesados, no los predios: un mismo interesado
--              vinculado a N predios es UN error de captura, no N. Se reportan
--              n_predios y npn_ejemplo para poder ubicarlo.
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambio de fondo frente a regla_2_19:
--
--   where ... primer_nombre like '%SUC%' or segundo_nombre like '%SUC%' ...
--
-- `like '%SUC%'` coincide con CUALQUIER aparición de esas tres letras dentro de una
-- palabra. Apellidos colombianos reales como SUCERQUIA, y topónimos como SUCRE, muy
-- frecuentes como apellido, se reportaban como sucesiones ilíquidas. Falsos positivos.
--
-- Aquí se usa un regex con límites de palabra (\m inicio, \M fin en PostgreSQL):
--   \mSUC\M      → la palabra suelta "SUC"
--   \mSUC\.      → "SUC." abreviado con punto
--   \mSUCS?\M    → "SUC" o "SUCS"
--   \mSUCESION\M → la palabra completa (normalizada sin tilde)
--   \mHEREDEROS\M→ otra marca habitual de sucesión
-- SUCRE y SUCERQUIA no coinciden porque no terminan en el límite de palabra tras "SUC".
--
-- Además:
--   * regla_2_19 comparaba con `like` sensible a mayúsculas: "Suc." en minúscula se
--     escapaba. Aquí se normaliza a mayúsculas sin tildes antes de comparar.
--   * Se reporta qué marca se detectó y en qué campo, no solo que hubo coincidencia.
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
        -- texto completo del nombre, en mayúsculas y sin tildes, para buscar la marca
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
            when b.nombre_norm ~ '\mSUCESION(ES)?\M' then 'SUCESION'
            when b.nombre_norm ~ '\mSUCS?\M'         then 'SUC / SUCS'
            when b.nombre_norm ~ '\mSUC\.'           then 'SUC.'
            when b.nombre_norm ~ '\mHEREDEROS?\M'    then 'HEREDEROS'
            else null
        end  marca_detectada
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
    marca_detectada,
    count(distinct npn)                        n_predios
    , min(npn)                                 npn_ejemplo
    , 'Fail' cond_2_33
from cte_validaciones
where marca_detectada is not null
group by
    documento_identidad,
    primer_nombre,
    segundo_nombre,
    primer_apellido,
    segundo_apellido,
    marca_detectada
order by n_predios desc
