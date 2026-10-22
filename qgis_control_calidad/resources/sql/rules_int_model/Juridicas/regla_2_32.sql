-- =============================================================================
-- Regla 2.32 — Nombres vs. razón social según tipo de interesado
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.32
-- Enunciado  : "Para los interesados que correspondan a "Persona Natural", deberán
--              diligenciarse los atributos "primer nombre", "segundo nombre", "primer
--              apellido" y "segundo apellido", los cuales no deben contener valores
--              numéricos ni caracteres especiales; en estos casos, el atributo "razón
--              social" no deberá diligenciarse. Para los interesados que correspondan
--              a "Persona Jurídica", los atributos "primer nombre", "segundo nombre",
--              "primer apellido" y "segundo apellido" no deberán diligenciarse; en su
--              lugar, únicamente deberá diligenciarse el atributo "razón social"."
-- Universo   : Interesados tipo Persona natural (hoja "Datos", id 35) y Persona
--              jurídica; en la práctica, todos los interesados con tipo asignado.
-- Falla si   : Persona natural:
--                val_pn_falta_1n           — primer_nombre vacío.
--                val_pn_falta_1a           — primer_apellido vacío.
--                (val_pn_falta_2n y _2a se calculan y se muestran, pero NO son
--                 condición de error — ver nota de obligatoriedad más abajo.)
--                val_pn_caracteres         — algún campo de nombre trae dígitos o
--                                            caracteres especiales.
--                val_pn_razon_social       — razon_social diligenciada.
--              Persona jurídica:
--                val_pj_razon_social       — razon_social vacía.
--                val_pj_nombres            — algún campo de nombre diligenciado.
-- No aplica  : interesados sin tipo asignado.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, col_miembros,
--              ilc_interesado, cr_interesadotipo
-- Origen     : CONSOLIDA regla_2_17 + regla_2_18 + regla_2_20 (set anterior)
-- Salida     : interesado_tipo, documento_identidad, nombres, razon_social, val_*, n_predios, npn_ejemplo, cond_2_32
-- Granularidad  : UNA fila por interesado. El universo declarado en la hoja "Datos"
--              del formato son los interesados, no los predios: un mismo interesado
--              vinculado a N predios es UN error de captura, no N. Se reportan
--              n_predios y npn_ejemplo para poder ubicarlo.
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 2 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Esta regla funde tres reglas del formato anterior y AÑADE un requisito que
-- ninguna cubría: que los nombres de persona natural estén efectivamente
-- diligenciados. Antes solo se validaba su contenido si existían.
--
-- OBLIGATORIEDAD DE LOS CAMPOS DE NOMBRE (criterio del área funcional, 2026-07-28):
-- solo **primer nombre y primer apellido** son obligatorios. Segundo nombre y segundo
-- apellido NO se exigen — no tenerlos es una situación civil corriente, no un error
-- de captura.
--
-- El enunciado enumera los cuatro atributos, pero exigirlos todos reportaba el 38 %
-- de las personas naturales de a_47189 (3 014 de 7 963) y el 29 % de xtf_mosquera
-- (1 727 de 6 001), casi todo por ausencia de segundo nombre. Ver H-21.
--
-- Los cuatro se calculan igual en val_pn_falta_1n / _2n / _1a / _2a y los cuatro se
-- muestran en el reporte; solo _1n y _1a participan en la condición de error. Así el
-- revisor ve la ausencia de segundo nombre sin que cuente como incumplimiento, y
-- reactivar la exigencia completa es agregar dos columnas al WHERE final.
--
-- El resto de la regla no cambia: contenido de los nombres (sin dígitos ni caracteres
-- especiales), razón social vacía en persona natural, y las dos validaciones de
-- persona jurídica.
--
-- Cambios frente a las reglas de origen:
--   * regla_2_18 y regla_2_20 deduplicaban con
--         row_number() over (partition by documento_identidad) ... where fila = 1
--     SIN ORDER BY. PostgreSQL puede elegir cualquier fila como la primera, así que
--     el resultado variaba entre ejecuciones y podía ocultar el registro defectuoso.
--     Se reemplaza por `distinct`, que es determinístico.
--   * El regex de regla_2_17, '^[a-zA-Z...][a-zA-Z...\s]*[a-zA-Z...]$', exige un
--     mínimo de DOS caracteres: un nombre de una sola letra se reportaba como error.
--     Se reemplaza por un patrón que admite nombres de un carácter y además acepta
--     apóstrofo y guion, presentes en apellidos reales (D'Achiardi, Pérez-Gómez).
--   * Se añaden Ü/ü y las mayúsculas acentuadas que faltaban en el patrón anterior.
-- =============================================================================

with cte_interesados as (
    select
        ip.numero_predial_nacional    npn,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        ii.primer_nombre, ii.segundo_nombre,
        ii.primer_apellido, ii.segundo_apellido,
        ii.razon_social,
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
        ii.razon_social,
        ii.tipo                       interesado_tipo_id
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}col_miembros cm       on cm.agrupacion = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cm.interesado_ilc_interesado
)
, cte_base as (
    select
        i.*,
        cit.ilicode                              interesado_tipo,
        coalesce(trim(i.primer_nombre),    '')   pn,
        coalesce(trim(i.segundo_nombre),   '')   sn,
        coalesce(trim(i.primer_apellido),  '')   pa,
        coalesce(trim(i.segundo_apellido), '')   sa,
        coalesce(trim(i.razon_social),     '')   rs
    from cte_interesados i
    join {esquema}{punto}cr_interesadotipo cit on cit.t_id = i.interesado_tipo_id
)
, cte_validaciones as (
    select
        b.*,
        -- Patrón de nombre válido: letras (con tildes y ñ/ü), espacios, apóstrofo y
        -- guion. Admite un solo carácter. Prohíbe dígitos y demás signos.
        -- el enunciado enumera los cuatro atributos; se validan por separado para
        -- que el reporte diga cuál falta
        case when b.interesado_tipo = 'Persona_Natural' and b.pn = ''
             then 'Fail' else 'Ok' end                       val_pn_falta_1n,
        case when b.interesado_tipo = 'Persona_Natural' and b.sn = ''
             then 'Fail' else 'Ok' end                       val_pn_falta_2n,
        case when b.interesado_tipo = 'Persona_Natural' and b.pa = ''
             then 'Fail' else 'Ok' end                       val_pn_falta_1a,
        case when b.interesado_tipo = 'Persona_Natural' and b.sa = ''
             then 'Fail' else 'Ok' end                       val_pn_falta_2a,

        case when b.interesado_tipo = 'Persona_Natural'
              and (   (b.pn <> '' and b.pn !~ '^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ ''-]*$')
                   or (b.sn <> '' and b.sn !~ '^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ ''-]*$')
                   or (b.pa <> '' and b.pa !~ '^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ ''-]*$')
                   or (b.sa <> '' and b.sa !~ '^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ ''-]*$'))
             then 'Fail' else 'Ok' end                       val_pn_caracteres,

        case when b.interesado_tipo = 'Persona_Natural' and b.rs <> ''
             then 'Fail' else 'Ok' end                       val_pn_razon_social,

        case when b.interesado_tipo = 'Persona_Juridica' and b.rs = ''
             then 'Fail' else 'Ok' end                       val_pj_razon_social,

        case when b.interesado_tipo = 'Persona_Juridica'
              and (b.pn <> '' or b.sn <> '' or b.pa <> '' or b.sa <> '')
             then 'Fail' else 'Ok' end                       val_pj_nombres
    from cte_base b
)
-- Se reporta UNA fila por interesado, no por predio: el universo declarado en
-- la hoja "Datos" del formato es el total de interesados. Un mismo interesado
-- vinculado a cientos de predios es UN error de captura, no cientos.
select
    interesado_tipo,
    documento_identidad,
    primer_nombre,
    segundo_nombre,
    primer_apellido,
    segundo_apellido,
    razon_social,
    val_pn_falta_1n,
    val_pn_falta_2n,
    val_pn_falta_1a,
    val_pn_falta_2a,
    val_pn_caracteres,
    val_pn_razon_social,
    val_pj_razon_social,
    val_pj_nombres,
    count(distinct npn)                        n_predios
    , min(npn)                                 npn_ejemplo
    , 'Fail' cond_2_32
from cte_validaciones
-- Solo primer nombre y primer apellido son obligatorios (criterio del área funcional,
-- 2026-07-28). val_pn_falta_2n y val_pn_falta_2a quedan como columnas INFORMATIVAS:
-- se calculan y se muestran, pero no disparan el error.
where 'Fail' in (val_pn_falta_1n, val_pn_falta_1a,
                 val_pn_caracteres, val_pn_razon_social,
                 val_pj_razon_social, val_pj_nombres)
group by
    interesado_tipo,
    documento_identidad,
    primer_nombre,
    segundo_nombre,
    primer_apellido,
    segundo_apellido,
    razon_social,
    val_pn_falta_1n,
    val_pn_falta_2n,
    val_pn_falta_1a,
    val_pn_falta_2a,
    val_pn_caracteres,
    val_pn_razon_social,
    val_pj_razon_social,
    val_pj_nombres
order by n_predios desc
