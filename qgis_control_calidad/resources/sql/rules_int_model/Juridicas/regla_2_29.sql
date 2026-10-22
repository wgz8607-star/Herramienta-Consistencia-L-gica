-- =============================================================================
-- Regla 2.29 — Persona natural: tipos de documento permitidos
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.29
-- Enunciado  : "Los interesados de tipo "Persona Natural" deben tener asociado
--              únicamente como tipo de documento: Cédula de Ciudadanía, Pasaporte,
--              Cédula de Extranjería, Tarjeta de Identidad, Registro Civil o número
--              secuencial (este último aplica exclusivamente cuando no fue posible
--              identificar el documento de identidad del interesado)."
-- Universo   : Interesados tipo Persona natural (hoja "Datos", id 35).
-- Falla si   : val_tipo_documento — el tipo de documento no está en la lista permitida
--                                   (en la práctica: es NIT).
--              val_documento_tipo_nulo — el interesado no tiene tipo de documento.
-- No aplica  : interesados Persona_Juridica (los valida 2.28).
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, cr_agrupacioninteresados,
--              col_miembros, ilc_interesado, cr_interesadotipo, cr_documentotipo
-- Origen     : regla_2_14.sql (set anterior)
-- Salida     : documento_identidad, nombre, interesado_tipo, documento_tipo, val_*, n_predios, npn_ejemplo, cond_2_29
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
-- CORRECCIÓN CRÍTICA (hallazgo H-01): regla_2_14 comparaba contra el literal 'CC':
--
--     and cd.ilicode NOT IN ('CC','Pasaporte','Cedula_Extranjeria',
--                            'Tarjeta_Identidad','Registro_Civil','Secuencial')
--
-- El enumerado CR_DocumentoTipo del modelo define 'Cedula_Ciudadania'; 'CC' no
-- existe. Consecuencia: TODO interesado con cédula de ciudadanía —la inmensa mayoría
-- del padrón— caía en el NOT IN y se reportaba como error. Falsos positivos masivos.
-- Aquí se usa el ilicode correcto.
--
-- Otros cambios frente a regla_2_14:
--   * Tipo de documento nulo se valida aparte (el NOT IN lo dejaba escapar).
--   * CTE con columnas nombradas en vez de `ii.*, cr.*`.
-- =============================================================================

with cte_interesados as (
    -- Camino 1: interesado asociado directamente al derecho.
    select
        ip.numero_predial_nacional    npn,
        'Directo'                     via,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido,
                       ii.razon_social)  nombre,
        ii.tipo                       interesado_tipo_id,
        ii.tipo_documento             documento_tipo_id
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cri.interesado_ilc_interesado

    union all

    -- Camino 2: interesados que son miembros de una agrupación asociada al derecho.
    select
        ip.numero_predial_nacional    npn,
        'Agrupación'                  via,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido,
                       ii.razon_social)  nombre,
        ii.tipo                       interesado_tipo_id,
        ii.tipo_documento             documento_tipo_id
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}col_miembros cm       on cm.agrupacion = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cm.interesado_ilc_interesado
)
, cte_base as (
    select
        i.npn,
        i.via,
        i.interesado_id,
        i.documento_identidad,
        i.nombre,
        cit.ilicode  interesado_tipo,
        cdt.ilicode  documento_tipo
    from cte_interesados i
    left join {esquema}{punto}cr_interesadotipo cit on cit.t_id = i.interesado_tipo_id
    left join {esquema}{punto}cr_documentotipo cdt  on cdt.t_id = i.documento_tipo_id
    where cit.ilicode = 'Persona_Natural'
)
, cte_validaciones as (
    select
        b.*,
        case when b.documento_tipo is null then 'Fail' else 'Ok' end  val_documento_tipo_nulo,
        case when coalesce(b.documento_tipo, '') not in ('Cedula_Ciudadania',
                                                         'Pasaporte',
                                                         'Cedula_Extranjeria',
                                                         'Tarjeta_Identidad',
                                                         'Registro_Civil',
                                                         'Secuencial')
             then 'Fail' else 'Ok' end                                val_tipo_documento
    from cte_base b
)
-- Se reporta UNA fila por interesado, no por predio: el universo declarado en
-- la hoja "Datos" del formato es el total de interesados. Un mismo interesado
-- vinculado a cientos de predios es UN error de captura, no cientos.
select
    documento_identidad,
    nombre,
    interesado_tipo,
    documento_tipo,
    val_documento_tipo_nulo,
    val_tipo_documento,
    count(distinct npn)                        n_predios
    , min(npn)                                 npn_ejemplo
    , 'Fail' cond_2_29
from cte_validaciones
where 'Fail' in (val_documento_tipo_nulo, val_tipo_documento)
group by
    documento_identidad,
    nombre,
    interesado_tipo,
    documento_tipo,
    val_documento_tipo_nulo,
    val_tipo_documento
order by n_predios desc
