-- =============================================================================
-- Regla 2.34 — El atributo sexo solo aplica a personas naturales
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.34
-- Enunciado  : "El atributo sexo del interesado debe diligenciarse únicamente para
--              personas naturales."
-- Universo   : Interesados tipo Persona natural (hoja "Datos", id 35) y jurídica.
-- Falla si   : val_pj_sexo — el interesado es Persona_Juridica y tiene sexo
--                            diligenciado.
--              val_pn_sexo — el interesado es Persona_Natural y NO tiene sexo
--                            diligenciado (el modelo exige identificarlo; si no se
--                            pudo, el valor es 'Sin_Determinar', no NULL).
-- No aplica  : interesados sin tipo asignado.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, col_miembros,
--              ilc_interesado, cr_interesadotipo, cr_sexotipo
-- Origen     : regla_2_21.sql (set anterior)
-- Salida     : documento_identidad, nombre, interesado_tipo, sexo, val_*, n_predios, npn_ejemplo, cond_2_34
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
-- Cambios frente a regla_2_21:
--   * El filtro era `cs.ilicode is not null and ci.ilicode <> 'Persona_Natural'`.
--     Con LEFT JOIN, si el tipo de interesado es NULL la comparación `<>` da NULL y
--     la fila no se reporta. Se hace explícito con `= 'Persona_Juridica'`.
--   * Se añade la validación inversa. La documentación del modelo dice: "La
--     identificación del sexo es obligatoria para las personas naturales. En el
--     evento que no sea posible identificar el sexo se debe asignar el dominio
--     'Sin_Determinar'". Es decir, una persona natural sin sexo diligenciado también
--     incumple. El enunciado del formato dice "únicamente para personas naturales",
--     que fija a quién aplica; la obligatoriedad la impone el modelo.
--     → Si el área funcional prefiere reportar solo el caso de persona jurídica,
--       basta con quitar val_pn_sexo del WHERE final.
-- =============================================================================

with cte_interesados as (
    select
        ip.numero_predial_nacional    npn,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido,
                       ii.razon_social)  nombre,
        ii.tipo                       interesado_tipo_id,
        ii.sexo                       sexo_id
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cri.interesado_ilc_interesado

    union all

    select
        ip.numero_predial_nacional    npn,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido,
                       ii.razon_social)  nombre,
        ii.tipo                       interesado_tipo_id,
        ii.sexo                       sexo_id
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
        i.nombre,
        cit.ilicode  interesado_tipo,
        cst.ilicode  sexo
    from cte_interesados i
    join      {esquema}{punto}cr_interesadotipo cit on cit.t_id = i.interesado_tipo_id
    left join {esquema}{punto}cr_sexotipo cst       on cst.t_id = i.sexo_id
)
, cte_validaciones as (
    select
        b.*,
        case when b.interesado_tipo = 'Persona_Juridica' and b.sexo is not null
             then 'Fail' else 'Ok' end   val_pj_sexo,
        case when b.interesado_tipo = 'Persona_Natural' and b.sexo is null
             then 'Fail' else 'Ok' end   val_pn_sexo
    from cte_base b
)
-- Se reporta UNA fila por interesado, no por predio: el universo declarado en
-- la hoja "Datos" del formato es el total de interesados. Un mismo interesado
-- vinculado a cientos de predios es UN error de captura, no cientos.
select
    documento_identidad,
    nombre,
    interesado_tipo,
    sexo,
    val_pj_sexo,
    val_pn_sexo,
    count(distinct npn)                        n_predios
    , min(npn)                                 npn_ejemplo
    , 'Fail' cond_2_34
from cte_validaciones
where 'Fail' in (val_pj_sexo, val_pn_sexo)
group by
    documento_identidad,
    nombre,
    interesado_tipo,
    sexo,
    val_pj_sexo,
    val_pn_sexo
order by n_predios desc
