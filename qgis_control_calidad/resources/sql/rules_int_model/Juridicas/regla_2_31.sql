-- =============================================================================
-- Regla 2.31 — Formato del NIT
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.31
-- Enunciado  : "Cuando el tipo de documento del interesado es "NIT", el número de
--              identificación debe estar diligenciado y ser diferente de cero o vacío,
--              contener únicamente caracteres numéricos, y permitir el uso del carácter
--              guion (-). El formato debe cumplir la estructura: solo números antes del
--              guion y un único dígito entero (0–9) después del guion. No se permiten
--              valores consecutivos o formatos inválidos como secuencias tipo 12345678-9."
-- Universo   : Interesados tipo Persona jurídica (hoja "Datos", id 34), restringido a
--              tipo de documento NIT.
-- Falla si   : val_diligenciado        — nulo o vacío.
--              val_no_cero             — solo ceros (con o sin dígito de verificación).
--              val_formato             — no cumple ^[0-9]{9}-[0-9]$ : la estructura
--                                        exigida es 9 dígitos + guion + 1 dígito.
--              val_longitud            — la parte antes del guion no tiene 9 dígitos.
--              val_no_secuencial       — los dígitos forman una secuencia consecutiva.
--              val_digito_verificacion — no trae guion + dígito de verificación.
-- No aplica  : cualquier otro tipo de documento.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, col_miembros,
--              ilc_interesado, cr_documentotipo
-- Origen     : regla_2_16.sql (set anterior) — REESCRITA: cambió la especificación.
-- Salida     : documento_identidad, razon_social, val_*, n_predios, npn_ejemplo, cond_2_31
-- Granularidad  : UNA fila por interesado. El universo declarado en la hoja "Datos"
--              del formato son los interesados, no los predios: un mismo interesado
--              vinculado a N predios es UN error de captura, no N. Se reportan
--              n_predios y npn_ejemplo para poder ubicarlo.
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 140 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- La especificación CAMBIÓ frente al formato anterior (hallazgo H-06):
--   Antes  : "mayor a 0, 10 caracteres incluido el dígito de verificación, sin
--             caracteres especiales, no consecutivo"  → regla_2_16 validaba ^\d{10}$
--   Ahora  : 9 dígitos + guion + 1 dígito de verificación → ^[0-9]{9}-[0-9]$
-- Son 10 dígitos en ambos casos; lo que cambia es que ahora el guion es parte
-- obligatoria del formato. El ^\d{10}$ de regla_2_16 rechazaba justamente los NIT
-- bien escritos.
--
-- IMPLEMENTACIÓN LITERAL DEL ENUNCIADO (decisión 2026-07-28)
--
-- 1. Estructura ESTRICTA 9-1: nueve dígitos, guion, un dígito de verificación
--    (criterio confirmado por el área funcional el 2026-07-28). El dígito de
--    verificación es obligatorio: el enunciado afirma "El formato debe cumplir la
--    estructura: solo números antes del guion y un único dígito entero (0–9)
--    después del guion", en imperativo.
--
--    IMPACTO MEDIDO: ningún NIT de las bases de prueba usa guion. Fallan 157/157 en
--    a_47189_00_20260410_mod_int y 2 136/2 136 en xtf_mosquera_20260330_20260407, es
--    decir el 100 %. Es consecuencia directa del enunciado, no un defecto de la regla:
--    los operadores capturan el NIT con el dígito de verificación pegado o sin él.
--    Ver docs/03_hallazgos.md H-06 y H-23.
--
-- 2. "Valores consecutivos": se implementa de forma general. Un número es una
--    secuencia consecutiva si es substring de '0123456789' (ascendente) o de
--    '9876543210' (descendente) — así `12345678` queda detectado sin necesidad de
--    enumerar casos. Se conservan además las secuencias de relleno que ya buscaba
--    regla_2_16 ('123456789', '987654321') por si aparecen embebidas.
-- =============================================================================

with cte_interesados as (
    select
        ip.numero_predial_nacional    npn,
        'Directo'                     via,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        ii.razon_social,
        ii.tipo_documento             documento_tipo_id
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cri.interesado_ilc_interesado

    union all

    select
        ip.numero_predial_nacional    npn,
        'Agrupación'                  via,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        ii.razon_social,
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
        i.razon_social,
        i.documento_identidad,
        trim(coalesce(i.documento_identidad, ''))              doc,
        -- parte numérica sin el dígito de verificación, para las validaciones de valor
        split_part(trim(coalesce(i.documento_identidad, '')), '-', 1)  doc_base
    from cte_interesados i
    join {esquema}{punto}cr_documentotipo cdt on cdt.t_id = i.documento_tipo_id
    where cdt.ilicode = 'NIT'
)
, cte_validaciones as (
    select
        b.*,
        case when b.doc = '' then 'Fail' else 'Ok' end                 val_diligenciado,
        case when b.doc <> '' and b.doc_base ~ '^0*$'
             then 'Fail' else 'Ok' end                                 val_no_cero,
        -- estructura exigida: EXACTAMENTE 9 dígitos, guion y 1 dígito de verificación
        case when b.doc <> '' and b.doc !~ '^[0-9]{9}-[0-9]$'
             then 'Fail' else 'Ok' end                                 val_formato,
        -- se separa la longitud para que el reporte distinga "no son 9 dígitos" de
        -- "no trae dígito de verificación"
        case when b.doc <> '' and length(b.doc_base) <> 9
             then 'Fail' else 'Ok' end                                 val_longitud,
        -- "no se permiten valores consecutivos": todo número cuyos dígitos forman una
        -- secuencia ascendente o descendente de 1 en 1 es substring de estas cadenas
        case when b.doc <> ''
              and (   length(b.doc_base) > 2
                      and (strpos('0123456789', b.doc_base) > 0
                        or strpos('9876543210', b.doc_base) > 0)
                   or b.doc like '%123456789%'
                   or b.doc like '%987654321%')
             then 'Fail' else 'Ok' end                                 val_no_secuencial,
        -- el dígito de verificación es obligatorio (ver nota 1 del encabezado)
        case when b.doc <> '' and b.doc !~ '-'
             then 'Fail' else 'Ok' end                                 val_digito_verificacion
    from cte_base b
)
-- Se reporta UNA fila por interesado, no por predio: el universo declarado en
-- la hoja "Datos" del formato es el total de interesados. Un mismo interesado
-- vinculado a cientos de predios es UN error de captura, no cientos.
select
    documento_identidad,
    razon_social,
    val_diligenciado,
    val_no_cero,
    val_formato,
    val_longitud,
    val_no_secuencial,
    val_digito_verificacion,
    count(distinct npn)                        n_predios
    , min(npn)                                 npn_ejemplo
    , 'Fail' cond_2_31
from cte_validaciones
where 'Fail' in (val_diligenciado, val_no_cero, val_formato, val_longitud,
                 val_no_secuencial, val_digito_verificacion)
group by
    documento_identidad,
    razon_social,
    val_diligenciado,
    val_no_cero,
    val_formato,
    val_longitud,
    val_no_secuencial,
    val_digito_verificacion
order by n_predios desc
