-- =============================================================================
-- Regla 2.30 — Número de documento diligenciado y válido (CC, CE, TI, RC)
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.30
-- Enunciado  : "Cuando el tipo de documento del interesado es "Cédula de Ciudadanía",
--              "Cédula de Extranjería", "Tarjeta de Identidad" o "Registro Civil", el
--              número de documento de identidad debe estar diligenciado y ser diferente
--              de cero o vacío. El uso de número secuencial solo esta permitido cuando
--              no haya sido posible identificar un documento de identidad del interesado."
-- Universo   : Interesados tipo Persona natural (hoja "Datos", id 35), restringido a
--              los tipos de documento CC, CE, TI y RC.
-- Falla si   : val_diligenciado — documento_identidad nulo o vacío.
--              val_no_cero      — documento_identidad es '0' o solo ceros.
--              val_numerico     — contiene caracteres no numéricos.
--              val_no_secuencial— es un consecutivo de relleno (123456789, 987654321).
-- No aplica  : documentos de tipo NIT (los valida 2.31), Pasaporte (admite letras)
--              y Secuencial (es un consecutivo por definición).
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, col_miembros,
--              ilc_interesado, cr_documentotipo
-- Origen     : regla_2_15.sql (set anterior)
-- Salida     : documento_tipo, documento_identidad, nombre, val_*, n_predios, npn_ejemplo, cond_2_30
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
-- CORRECCIÓN CRÍTICA (hallazgo H-01): regla_2_15 filtraba con
--
--     where cd.ilicode IN ('CC','Cedula_Extranjeria','Tarjeta_Identidad','Registro_Civil')
--
-- 'CC' no existe en CR_DocumentoTipo; el valor correcto es 'Cedula_Ciudadania'. Por
-- eso la regla NUNCA evaluaba las cédulas de ciudadanía, que son el tipo de documento
-- más frecuente. Falsos negativos.
--
-- Otros cambios frente a regla_2_15:
--   * `documento_identidad !~ '^[0-9]*$'` acepta la cadena VACÍA como válida, porque
--     `*` admite cero repeticiones. Un documento en blanco pasaba la validación pese
--     a que el enunciado lo prohíbe explícitamente. Se separa en dos condiciones:
--     "está diligenciado" y "es numérico" (`^[0-9]+$`).
--   * `= '0'` solo capturaba el cero exacto; '00', '000' se escapaban. Se generaliza.
--   * Se añade el nombre al resultado para poder ubicar el registro.
-- =============================================================================

with cte_interesados as (
    select
        ip.numero_predial_nacional    npn,
        'Directo'                     via,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido)  nombre,
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
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido)  nombre,
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
        i.nombre,
        i.documento_identidad,
        trim(coalesce(i.documento_identidad, ''))  doc,
        cdt.ilicode                                documento_tipo
    from cte_interesados i
    join {esquema}{punto}cr_documentotipo cdt on cdt.t_id = i.documento_tipo_id
    where cdt.ilicode in ('Cedula_Ciudadania',
                          'Cedula_Extranjeria',
                          'Tarjeta_Identidad',
                          'Registro_Civil')
)
, cte_validaciones as (
    select
        b.*,
        case when b.doc = '' then 'Fail' else 'Ok' end                  val_diligenciado,
        -- '0', '00', '000'... todos equivalen a documento no identificado
        case when b.doc <> '' and b.doc ~ '^0+$'
             then 'Fail' else 'Ok' end                                  val_no_cero,
        -- '+' en vez de '*': la cadena vacía ya no cuenta como numérica válida
        case when b.doc <> '' and b.doc !~ '^[0-9]+$'
             then 'Fail' else 'Ok' end                                  val_numerico,
        case when b.doc like '%123456789%' or b.doc like '%987654321%'
             then 'Fail' else 'Ok' end                                  val_no_secuencial
    from cte_base b
)
-- Se reporta UNA fila por interesado, no por predio: el universo declarado en
-- la hoja "Datos" del formato es el total de interesados. Un mismo interesado
-- vinculado a cientos de predios es UN error de captura, no cientos.
select
    documento_tipo,
    documento_identidad,
    nombre,
    val_diligenciado,
    val_no_cero,
    val_numerico,
    val_no_secuencial,
    count(distinct npn)                        n_predios
    , min(npn)                                 npn_ejemplo
    , 'Fail' cond_2_30
from cte_validaciones
where 'Fail' in (val_diligenciado, val_no_cero, val_numerico, val_no_secuencial)
group by
    documento_tipo,
    documento_identidad,
    nombre,
    val_diligenciado,
    val_no_cero,
    val_numerico,
    val_no_secuencial
order by n_predios desc
