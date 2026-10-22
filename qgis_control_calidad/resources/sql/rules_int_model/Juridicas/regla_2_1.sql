-- =============================================================================
-- Regla 2.1 — Coherencia entre tipo de derecho y tipo de predio
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.1
-- Enunciado  : "Los predios con un tipo de derecho "Ocupación" deben estar asociados
--              a predios de tipo "Público" y los predios con un tipo de derecho
--              "Posesión" deben estar asociados a predios de tipo "Privado"."
-- Universo   : Predios tipo públicos (hoja "Datos", id 28); en la práctica se evalúan
--              todos los predios con derecho de Ocupación o de Posesión.
-- Falla si   : val_ocupacion — derecho 'Ocupacion' sobre un predio que no es
--                              Predio.Publico.*
--              val_posesion  — derecho 'Posesion' sobre un predio que no es
--                              Predio.Privado.*
-- No aplica  : derechos de Dominio (su coherencia la validan 2.2, 2.4, 2.7, 2.11,
--              2.12 y 2.15); predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo
-- Origen     : CONSOLIDA regla_2_3 + regla_2_4 + regla_2_5 (set anterior)
-- Salida     : npn, predio_tipo, derecho_tipo, val_*, cond_2_1
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Esta regla funde tres reglas del formato anterior:
--   regla_2_3 — Posesión ⇒ tipo de predio Privado
--   regla_2_4 — tipo de predio Privado ⇒ no puede tener Ocupación
--   regla_2_5 — tipo de predio público ⇒ no puede tener Posesión
-- Las tres expresaban la misma correspondencia desde ángulos distintos. El enunciado
-- nuevo la enuncia de forma directa y bidireccional.
--
-- Se usa `like 'Predio.Publico.%'` y `like 'Predio.Privado.%'` en vez de listar los
-- subtipos: el enumerado ILC_PredioTipo es jerárquico y así la regla no se rompe si
-- se agrega un subtipo nuevo. regla_2_4 listaba explícitamente
-- ('Predio.Privado.Privado','Predio.Privado.Colectivo') y habría dejado fuera
-- cualquier subtipo futuro.
--
-- Nota: la regla actual regla_2_34 (coherencia entre el dígito 22 del NPN y el tipo
-- de derecho) NO se integra aquí. Se descartó por decisión del 2026-07-28: no tiene
-- equivalente en el formato vigente. Ver docs/03_hallazgos.md D-01.
-- =============================================================================

with cte_base as (
    select
        ip.numero_predial_nacional    npn,
        substring(ip.numero_predial_nacional, 22, 1)  pos_22,
        ipt.ilicode                   predio_tipo,
        idt.ilicode                   derecho_tipo
    from {esquema}{punto}ilc_predio ip
    join      {esquema}{punto}ilc_derecho ide              on ide.unidad = ip.t_id
    left join {esquema}{punto}ilc_prediotipo ipt           on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_derechocatastraltipo idt on idt.t_id = ide.tipo
    where idt.ilicode in ('Ocupacion', 'Posesion')
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
        -- coalesce: un tipo de predio nulo también incumple, y sin él la comparación
        -- daría NULL y la fila no se reportaría
        case when b.derecho_tipo = 'Ocupacion'
              and coalesce(b.predio_tipo, '') not like 'Predio.Publico.%'
             then 'Fail' else 'Ok' end   val_ocupacion,
        case when b.derecho_tipo = 'Posesion'
              and coalesce(b.predio_tipo, '') not like 'Predio.Privado.%'
             then 'Fail' else 'Ok' end   val_posesion
    from cte_base b
)
select distinct
    npn,
    pos_22,
    predio_tipo,
    derecho_tipo,
    val_ocupacion,
    val_posesion,
    'Fail' cond_2_1
from cte_validaciones
where 'Fail' in (val_ocupacion, val_posesion)
