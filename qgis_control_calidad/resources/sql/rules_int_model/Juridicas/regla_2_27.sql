-- =============================================================================
-- Regla 2.27 — Condición Vía o Bien de Uso Público ⇒ tipo Uso Público y Dominio
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.27
-- Enunciado  : "Cuando la condición del predio corresponda a "Vía" o "Bien de Uso
--              Público" el tipo de predio debe ser "Uso Público" y el tipo de derecho
--              debe ser "Dominio"."
-- Universo   : Predios tipo Vía y de Uso Público (hoja "Datos", id 33).
-- Falla si   : val_tipo_predio  — tipo <> Predio.Publico.Uso_Publico (o nulo).
--              val_derecho      — tipo de derecho <> Dominio (o nulo).
--              val_existe_derecho — el predio no tiene derecho asociado.
-- No aplica  : predios con otra condición; predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_condicionprediotipo, ilc_prediotipo, ilc_derecho,
--              ilc_derechocatastraltipo
-- Origen     : regla_2_10.sql (set anterior)
-- Salida     : npn, condicion_predio, predio_tipo, derecho_tipo, val_*, cond_2_27
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambios frente a regla_2_10:
--   * El WHERE anterior era `ip2.ilicode <> '...' or id2.ilicode <> 'Dominio'`. Con
--     LEFT JOIN, si el tipo de predio o el tipo de derecho vienen nulos, `<>` evalúa
--     a NULL y la fila NO se reporta. Es decir: los predios a los que les falta
--     justamente el dato que la regla exige se escapaban. Se reemplaza por
--     `is distinct from`, que trata NULL como valor distinto.
--   * Se separan las dos condiciones del enunciado en val_* independientes.
--   * Se detecta explícitamente el predio sin ningún derecho asociado.
-- =============================================================================

with cte_base as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        icp.ilicode                   condicion_predio,
        ipt.ilicode                   predio_tipo,
        ide.t_id                      derecho_id,
        idt.ilicode                   derecho_tipo
    from {esquema}{punto}ilc_predio ip
    join      {esquema}{punto}ilc_condicionprediotipo icp  on icp.t_id = ip.condicion_predio
    left join {esquema}{punto}ilc_prediotipo ipt           on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_derecho ide              on ide.unidad = ip.t_id
    left join {esquema}{punto}ilc_derechocatastraltipo idt on idt.t_id = ide.tipo
    where icp.ilicode in ('Via', 'Bien_Uso_Publico')
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
        case when b.predio_tipo is distinct from 'Predio.Publico.Uso_Publico'
             then 'Fail' else 'Ok' end                       val_tipo_predio,
        case when b.derecho_id is null then 'Fail' else 'Ok' end  val_existe_derecho,
        case when b.derecho_id is not null
              and b.derecho_tipo is distinct from 'Dominio'
             then 'Fail' else 'Ok' end                       val_derecho
    from cte_base b
)
select distinct
    npn,
    condicion_predio,
    predio_tipo,
    derecho_tipo,
    val_tipo_predio,
    val_existe_derecho,
    val_derecho,
    'Fail' cond_2_27
from cte_validaciones
where 'Fail' in (val_tipo_predio, val_existe_derecho, val_derecho)
