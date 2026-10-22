-- =============================================================================
-- Regla 2.40 — Predio con más de un interesado exige registro de agrupación
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.40
-- Enunciado  : "Todo predio con más de un interesado debe contar con su respectivo
--              registro en la tabla cr_agrupacioninteresados."
-- Universo   : Predios con más de un interesado asociado.
-- Falla si   : val_agrupacion — el predio tiene 2 o más interesados relacionados de
--                               forma INDIVIDUAL (col_rrrinteresado.interesado_ilc_interesado)
--                               y ninguna agrupación registrada.
--              val_doble_via  — el predio relaciona sus interesados por las dos vías
--                               a la vez (individual y por agrupación).
-- No aplica  : predios con un solo interesado; predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, cr_agrupacioninteresados,
--              col_miembros
-- Origen     : regla_2_33.sql (set anterior)
-- Salida     : npn, n_individuales, n_agrupaciones, n_miembros_agrupacion,
--              situacion, cond_2_40
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Reescritura estructural. regla_2_33 construía dos CTE y los unía con FULL OUTER
-- JOIN sobre el NPN, y su CASE tenía ramas inalcanzables:
--
--     WHEN t0.cantidad_interesados IS NULL THEN 'Relacion rota predio-interesado'
--
--   ...pero esa condición ya la había capturado una rama anterior
--   (`when t0... is null and t2... is not null`), de modo que 'Relacion rota' y las
--   dos últimas ramas nunca se alcanzaban. También clasificaba como
--   'Fail - Interesados asociados doble vez' cualquier caso en que los conteos
--   coincidieran por casualidad, que no es lo mismo que estar duplicado.
--
-- Aquí se cuenta por predio en un solo paso y se clasifica de forma exhaustiva y
-- mutuamente excluyente.
-- =============================================================================

with cte_conteos as (
    select
        ip.t_id                                                    predio_id,
        ip.numero_predial_nacional                                 npn,
        -- interesados relacionados individualmente al derecho
        count(distinct cri.interesado_ilc_interesado)              n_individuales,
        -- agrupaciones relacionadas al derecho
        count(distinct cri.interesado_cr_agrupacioninteresados)    n_agrupaciones,
        -- miembros efectivos dentro de esas agrupaciones
        count(distinct cm.interesado_ilc_interesado)               n_miembros_agrupacion
    from {esquema}{punto}ilc_predio ip
    left join {esquema}{punto}ilc_derecho ide       on ide.unidad = ip.t_id
    left join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    left join {esquema}{punto}col_miembros cm
           on cm.agrupacion = cri.interesado_cr_agrupacioninteresados
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
    group by ip.t_id, ip.numero_predial_nacional
)
, cte_validaciones as (
    select
        c.*,
        -- Más de un interesado individual y ninguna agrupación: es el defecto que
        -- describe el enunciado.
        case when c.n_individuales > 1 and c.n_agrupaciones = 0
             then 'Fail' else 'Ok' end   val_agrupacion,
        -- Las dos vías a la vez: el mismo predio relaciona interesados sueltos y por
        -- agrupación. El modelo lo permite estructuralmente pero indica captura
        -- inconsistente y produce dobles conteos aguas abajo.
        case when c.n_individuales > 0 and c.n_agrupaciones > 0
             then 'Fail' else 'Ok' end   val_doble_via,
        -- Agrupación registrada pero vacía: no es lo que pide el enunciado, se
        -- expone como información porque invalida el conteo de interesados.
        case when c.n_agrupaciones > 0 and c.n_miembros_agrupacion = 0
             then 'Fail' else 'Ok' end   val_agrupacion_vacia
    from cte_conteos c
)
select
    npn,
    n_individuales,
    n_agrupaciones,
    n_miembros_agrupacion,
    case
        when val_agrupacion       = 'Fail' then 'Varios interesados sin agrupación registrada'
        when val_doble_via        = 'Fail' then 'Interesados relacionados por las dos vías'
        when val_agrupacion_vacia = 'Fail' then 'Agrupación registrada sin miembros'
    end  situacion,
    val_agrupacion,
    val_doble_via,
    val_agrupacion_vacia,
    'Fail' cond_2_40
from cte_validaciones
where 'Fail' in (val_agrupacion, val_doble_via, val_agrupacion_vacia)
