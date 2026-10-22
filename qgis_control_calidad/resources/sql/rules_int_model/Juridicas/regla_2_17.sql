-- =============================================================================
-- Regla 2.17 — Fecha de inicio de tenencia diligenciada y anterior a la visita
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.17
-- Enunciado  : "La fecha de inicio de la tenencia asociada al derecho debe estar
--              diligenciada y deber ser anterior a la fecha de la visita al predio."
-- Universo   : Total de derechos (hoja "Datos", id 24).
-- Falla si   : val_diligenciada — fecha_inicio_tenencia es NULL.
--              val_anterior_visita — fecha_inicio_tenencia >= fecha_visita_predial.
--              val_rango — fecha_inicio_tenencia anterior a 1900-01-01 (dato imposible).
-- No aplica  : predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_derecho, ilc_datosadicionaleslevantamientocatastral,
--              ilc_estructuranovedadnumeropredial(+_tipo_novedad)
-- Origen     : regla_2_1.sql (set anterior) — se divide: la excepción 1936/1959 pasa a 2.19.
-- Salida     : npn, fecha_inicio_tenencia, fecha_visita_predial, val_*, cond_2_17
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Nota: la regla anterior mezclaba en un solo CASE la validación general y la
-- excepción de predios con Dominio sin FMI (fechas 1936-12-04 / 1959-12-31). El
-- formato nuevo las separa: aquí queda la general, en 2.19 la de fechas normativas.
-- Por eso los predios que caen en el supuesto de 2.19 se excluyen de esta regla:
-- 1936 y 1959 son anteriores a la visita, así que pasarían igual, pero dejarlos
-- fuera evita reportar dos veces el mismo predio si la fecha está mal.
-- =============================================================================

with cte_base as (
    -- Un registro por derecho. La fecha de visita vive en datos adicionales del predio.
    select
        ip.t_id                        predio_id,
        ip.numero_predial_nacional     npn,
        ide.t_id                       derecho_id,
        idt.ilicode                    derecho_tipo,
        ip.matricula_inmobiliaria      fmi,
        ide.fecha_inicio_tenencia      fecha_inicio_tenencia,
        ida.fecha_visita_predial       fecha_visita_predial
    from {esquema}{punto}ilc_predio ip
    join      {esquema}{punto}ilc_derecho ide              on ide.unidad = ip.t_id
    left join {esquema}{punto}ilc_derechocatastraltipo idt on idt.t_id = ide.tipo
    left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral ida
           on ida.ilc_predio = ip.t_id
    where
        -- excluir predios cancelados: ya no deben cumplir coherencia jurídica
        not exists (
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
        -- excluir el supuesto de la regla 2.19 (Dominio sin FMI en Uso_Publico /
        -- Presunto_Baldio), que exige fechas normativas fijas y se valida allá
        and not (
            idt.ilicode = 'Dominio'
            and coalesce(ip.matricula_inmobiliaria, 0) = 0
            and exists (
                select 1
                from {esquema}{punto}ilc_prediotipo ipt
                where ipt.t_id = ip.tipo
                  and ipt.ilicode in ('Predio.Publico.Uso_Publico',
                                      'Predio.Publico.Presunto_Baldio')
            )
        )
)
, cte_validaciones as (
    select
        b.*,
        case when b.fecha_inicio_tenencia is null
             then 'Fail' else 'Ok' end                                      val_diligenciada,
        -- si no hay fecha de visita registrada no se puede comparar: no se marca error aquí,
        -- esa ausencia la reporta el componente administrativo
        case when b.fecha_inicio_tenencia is not null
              and b.fecha_visita_predial  is not null
              and b.fecha_inicio_tenencia >= b.fecha_visita_predial
             then 'Fail' else 'Ok' end                                      val_anterior_visita,
        case when b.fecha_inicio_tenencia is not null
              and b.fecha_inicio_tenencia < date '1900-01-01'
             then 'Fail' else 'Ok' end                                      val_rango
    from cte_base b
)
select distinct
    npn,
    derecho_tipo,
    fmi,
    fecha_inicio_tenencia,
    fecha_visita_predial,
    val_diligenciada,
    val_anterior_visita,
    val_rango,
    'Fail' cond_2_17
from cte_validaciones
where 'Fail' in (val_diligenciada, val_anterior_visita, val_rango)
