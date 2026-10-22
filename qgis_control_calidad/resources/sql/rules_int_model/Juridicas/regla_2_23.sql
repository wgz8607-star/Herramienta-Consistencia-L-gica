-- =============================================================================
-- Regla 2.23 — Todo predio debe tener interesado o agrupación de interesados
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.23
-- Enunciado  : "Todo predio debe tener asociado al menos un interesado o una
--              agrupación de interesados."
-- Universo   : Total de interesados (hoja "Datos", id 41); en la práctica se evalúa
--              predio por predio.
-- Falla si   : val_derecho    — el predio no tiene ningún derecho asociado.
--              val_interesado — ninguno de sus derechos apunta a un interesado ni a
--                               una agrupación en col_rrrinteresado.
-- No aplica  : predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado
-- Origen     : regla_2_29.sql (set anterior)
-- Salida     : npn, predio_tipo, n_derechos, n_interesados, n_agrupaciones,
--              val_derecho, val_interesado, cond_2_23
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambios frente a regla_2_29:
--   * La regla anterior evaluaba fila a fila: un predio con dos derechos, uno con
--     interesado y otro sin él, se reportaba como error aunque SÍ tiene interesado.
--     El enunciado pide "al menos uno", que es una condición POR PREDIO. Aquí se
--     agrega primero y se evalúa después.
--   * Se distingue "no tiene derechos" de "tiene derechos sin interesado": son
--     defectos distintos y se corrigen de forma distinta.
--   * Se reportan los conteos para que el revisor vea de inmediato la situación.
-- =============================================================================

with cte_base as (
    -- Un registro por predio, con el conteo de sus derechos e interesados.
    select
        ip.t_id                                                   predio_id,
        ip.numero_predial_nacional                                npn,
        ipt.ilicode                                               predio_tipo,
        count(distinct ide.t_id)                                  n_derechos,
        count(distinct cri.interesado_ilc_interesado)             n_interesados,
        count(distinct cri.interesado_cr_agrupacioninteresados)   n_agrupaciones
    from {esquema}{punto}ilc_predio ip
    left join {esquema}{punto}ilc_prediotipo ipt      on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_derecho ide         on ide.unidad = ip.t_id
    left join {esquema}{punto}col_rrrinteresado cri   on cri.rrr = ide.t_id
    where not exists (
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
    group by ip.t_id, ip.numero_predial_nacional, ipt.ilicode
)
, cte_validaciones as (
    select
        b.*,
        case when b.n_derechos = 0 then 'Fail' else 'Ok' end   val_derecho,
        case when b.n_interesados = 0 and b.n_agrupaciones = 0
             then 'Fail' else 'Ok' end                         val_interesado
    from cte_base b
)
select
    npn,
    predio_tipo,
    n_derechos,
    n_interesados,
    n_agrupaciones,
    val_derecho,
    val_interesado,
    'Fail' cond_2_23
from cte_validaciones
where 'Fail' in (val_derecho, val_interesado)
