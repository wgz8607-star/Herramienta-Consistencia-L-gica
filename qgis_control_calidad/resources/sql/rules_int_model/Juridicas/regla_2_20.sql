-- =============================================================================
-- Regla 2.20 — Datos de fuente administrativa obligatorios en predios con FMI
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.20
-- Enunciado  : "Cuando el predio tiene folio de matrícula inmobiliaria en la tabla
--              ILC_Predio, debe contar con fecha de documento fuente, tipo de fuente
--              administrativa, número de fuente administrativa y ente emisor
--              registrados. Adicionalmente, la fecha de documento fuente no puede ser
--              posterior a la fecha de visita al predio."
-- Universo   : Predios con matrícula inmobiliaria diligenciada (hoja "Datos", id 9).
-- Falla si   : val_existe_fuente — el derecho no tiene fuente administrativa asociada.
--              val_tipo         — ilc_fuenteadministrativa.tipo nulo.
--              val_numero       — numero_fuente nulo o vacío.
--              val_ente         — ente_emisor nulo o vacío.
--              val_fecha        — fecha_documento_fuente nula.
--              val_fecha_visita — fecha_documento_fuente > fecha_visita_predial.
-- No aplica  : predios sin FMI; predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrfuente, ilc_fuenteadministrativa,
--              col_fuenteadministrativatipo, ilc_datosadicionaleslevantamientocatastral
-- Origen     : regla_2_12.sql (set anterior)
-- Salida     : npn, fmi, fuente_tipo, ente_emisor, numero_fuente,
--              fecha_documento_fuente, fecha_visita_predial, val_*, cond_2_20
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 1 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambios frente a regla_2_12:
--   * Se descomponen las 6 condiciones en columnas val_* para que el reporte diga
--     cuál campo falta. Antes todo era un OR y el revisor tenía que deducirlo.
--   * Se detecta el caso "el derecho no tiene NINGUNA fuente asociada", que el OR
--     anterior capturaba por accidente (los LEFT JOIN dejan todo en NULL) pero sin
--     distinguirlo de "hay fuente con campos vacíos".
--   * numero_fuente y ente_emisor se validan también contra cadena vacía, no solo NULL.
--   * "Tiene FMI" pasa a coalesce(...) <> 0: regla_2_12 solo pedía IS NOT NULL, así
--     que los predios con matrícula = 0 (equivalente a no tener FMI) entraban al
--     universo y se reportaban como error.
-- =============================================================================

with cte_base as (
    select
        ip.t_id                        predio_id,
        ip.numero_predial_nacional     npn,
        ip.matricula_inmobiliaria      fmi,
        ide.t_id                       derecho_id,
        ifa.t_id                       fuente_id,
        cft.ilicode                    fuente_tipo,
        ifa.ente_emisor                ente_emisor,
        ifa.numero_fuente              numero_fuente,
        ifa.fecha_documento_fuente     fecha_documento_fuente,
        ida.fecha_visita_predial       fecha_visita_predial
    from {esquema}{punto}ilc_predio ip
    join      {esquema}{punto}ilc_derecho ide                on ide.unidad = ip.t_id
    left join {esquema}{punto}col_rrrfuente crf              on crf.rrr = ide.t_id
    left join {esquema}{punto}ilc_fuenteadministrativa ifa   on ifa.t_id = crf.fuente_administrativa
    left join {esquema}{punto}col_fuenteadministrativatipo cft on cft.t_id = ifa.tipo
    left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral ida
           on ida.ilc_predio = ip.t_id
    where coalesce(ip.matricula_inmobiliaria, 0) <> 0
      and not exists (
            select 1
            from {esquema}{punto}ilc_datosadicionaleslevantamientocatastral ida2
            join {esquema}{punto}ilc_estructuranovedadnumeropredial ie
              on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = ida2.t_id
            join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn
              on ietn.t_id = ie.tipo_novedad
            where ida2.ilc_predio = ip.t_id
              and ietn.ilicode in ('Cancelacion',
                                   'Cancelacion_por_Englobe',
                                   'Cancelacion_por_Desenglobe')
      )
)
, cte_validaciones as (
    select
        b.*,
        case when b.fuente_id is null then 'Fail' else 'Ok' end   val_existe_fuente,
        case when b.fuente_id is not null and b.fuente_tipo is null
             then 'Fail' else 'Ok' end                            val_tipo,
        case when b.fuente_id is not null
              and coalesce(trim(b.numero_fuente::text), '') = ''
             then 'Fail' else 'Ok' end                            val_numero,
        case when b.fuente_id is not null
              and coalesce(trim(b.ente_emisor), '') = ''
             then 'Fail' else 'Ok' end                            val_ente,
        case when b.fuente_id is not null and b.fecha_documento_fuente is null
             then 'Fail' else 'Ok' end                            val_fecha,
        case when b.fecha_documento_fuente is not null
              and b.fecha_visita_predial   is not null
              and b.fecha_documento_fuente > b.fecha_visita_predial
             then 'Fail' else 'Ok' end                            val_fecha_visita
    from cte_base b
)
select distinct
    npn,
    fmi,
    fuente_tipo,
    ente_emisor,
    numero_fuente,
    fecha_documento_fuente,
    fecha_visita_predial,
    val_existe_fuente,
    val_tipo,
    val_numero,
    val_ente,
    val_fecha,
    val_fecha_visita,
    'Fail' cond_2_20
from cte_validaciones
where 'Fail' in (val_existe_fuente, val_tipo, val_numero,
                 val_ente, val_fecha, val_fecha_visita)
