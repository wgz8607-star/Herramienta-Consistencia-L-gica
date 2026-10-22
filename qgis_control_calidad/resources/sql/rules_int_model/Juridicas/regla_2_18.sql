-- =============================================================================
-- Regla 2.18 — Tenencia posterior a la inscripción del título (predios con FMI)
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.18
-- Enunciado  : "Para predios con folio de matrícula inmobiliaria, la fecha de inicio
--              de tenencia asociada al derecho debe ser mayor o igual a la fecha de
--              inscripción del título (documento fuente)."
-- Universo   : Predios con matrícula inmobiliaria diligenciada (hoja "Datos", id 9).
-- Falla si   : val_orden — fecha_inicio_tenencia < fecha_documento_fuente.
--              val_fecha_fuente — el predio tiene FMI pero la fuente no tiene fecha
--                                 (sin ella la comparación es imposible; 2.20 valida
--                                 la ausencia, aquí solo se deja visible).
-- No aplica  : predios sin FMI; predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_derecho, ilc_derechocatastraltipo, col_rrrfuente,
--              ilc_fuenteadministrativa, col_fuenteadministrativatipo
-- Origen     : regla_2_11.sql (set anterior)
-- Salida     : npn, fmi, derecho_tipo, fuente_tipo, fecha_inicio_tenencia,
--              fecha_documento_fuente, cond_2_18
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 39 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambios frente a regla_2_11:
--   * El enunciado nuevo NO restringe a derecho Dominio; el filtro es tener FMI.
--     regla_2_11 filtraba `id2.ilicode = 'Dominio'` y dejaba fuera los informales
--     con FMI, que el propio formato reconoce como caso posible (regla 2.16).
--   * Se añade `distinct`: un derecho puede tener varias fuentes administrativas y
--     un predio varios derechos, lo que multiplicaba filas en el resultado anterior.
--   * "Sin FMI" pasa a evaluarse con coalesce(...) = 0 en vez de comparar contra '0'.
-- =============================================================================

with cte_base as (
    -- Un registro por (derecho × fuente administrativa) de predios con FMI.
    select
        ip.numero_predial_nacional     npn,
        ip.matricula_inmobiliaria      fmi,
        idt.ilicode                    derecho_tipo,
        cft.ilicode                    fuente_tipo,
        ide.fecha_inicio_tenencia      fecha_inicio_tenencia,
        ifa.fecha_documento_fuente     fecha_documento_fuente
    from {esquema}{punto}ilc_predio ip
    join      {esquema}{punto}ilc_derecho ide                on ide.unidad = ip.t_id
    left join {esquema}{punto}ilc_derechocatastraltipo idt   on idt.t_id = ide.tipo
    left join {esquema}{punto}col_rrrfuente crf              on crf.rrr = ide.t_id
    left join {esquema}{punto}ilc_fuenteadministrativa ifa   on ifa.t_id = crf.fuente_administrativa
    left join {esquema}{punto}col_fuenteadministrativatipo cft on cft.t_id = ifa.tipo
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
        case when b.fecha_inicio_tenencia  is not null
              and b.fecha_documento_fuente is not null
              and b.fecha_inicio_tenencia  < b.fecha_documento_fuente
             then 'Fail' else 'Ok' end                          val_orden,
        -- Fuente asociada pero sin fecha: la comparación no se puede hacer.
        -- No se marca como error de esta regla (lo reporta 2.20); se expone para
        -- que quien revisa entienda por qué val_orden quedó en 'Ok'.
        case when b.fuente_tipo is not null
              and b.fecha_documento_fuente is null
             then 'Fail' else 'Ok' end                          val_fecha_fuente
    from cte_base b
)
select distinct
    npn,
    fmi,
    derecho_tipo,
    fuente_tipo,
    fecha_inicio_tenencia,
    fecha_documento_fuente,
    val_orden,
    val_fecha_fuente,
    'Fail' cond_2_18
from cte_validaciones
where val_orden = 'Fail'
