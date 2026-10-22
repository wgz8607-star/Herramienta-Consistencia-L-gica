-- =============================================================================
-- Regla 2.26 — Predio "Privado colectivo" exige grupo étnico en el interesado
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.26
-- Enunciado  : "Cuando el predio es catalogado como "Privado colectivo", el interesado
--              debe tener diligenciado el campo Grupo Étnico y su valor debe ser
--              diferente de "Ninguno"."
-- Universo   : Predios tipo Predio.Privado.Colectivo (hoja "Datos", id 30 — ver
--              nota H-05: esa fila apunta por error a la regla 2.41).
-- Falla si   : val_grupo_etnico — el interesado tiene grupo_etnico nulo o 'Ninguno'.
-- No aplica  : predios de cualquier otro tipo; predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, col_rrrinteresado,
--              ilc_interesado, ilc_autorreconocimientoetnicotipo, cr_agrupacioninteresados,
--              col_miembros
-- Origen     : regla_2_7.sql (set anterior)
-- Salida     : npn, predio_tipo, documento_identidad, nombre, grupo_etnico, cond_2_26
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambios frente a regla_2_7:
--   * regla_2_7 solo miraba `cr.interesado_ilc_interesado`. Si el predio colectivo
--     tenía una AGRUPACIÓN de interesados (lo habitual en territorios colectivos:
--     consejos comunitarios, resguardos), la fila quedaba con interesado NULL, el
--     grupo étnico también NULL y se reportaba como error — falso positivo — sin
--     llegar a revisar los miembros reales. Ahora se recorren ambos caminos:
--     interesado individual y miembros de la agrupación.
--   * Se identifica al interesado en la salida (documento y nombre); antes solo se
--     veía el NPN y no se sabía a quién corregir.
-- =============================================================================

with cte_predios_colectivos as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        ipt.ilicode                   predio_tipo
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_prediotipo ipt on ipt.t_id = ip.tipo
    where ipt.ilicode = 'Predio.Privado.Colectivo'
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
, cte_interesados as (
    -- Camino 1: interesado asociado directamente al derecho.
    select
        pc.predio_id,
        pc.npn,
        pc.predio_tipo,
        'Directo'                     via,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido,
                       ii.razon_social)  nombre,
        iae.ilicode                   grupo_etnico
    from cte_predios_colectivos pc
    join {esquema}{punto}ilc_derecho ide            on ide.unidad = pc.predio_id
    join {esquema}{punto}col_rrrinteresado cri      on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii          on ii.t_id = cri.interesado_ilc_interesado
    left join {esquema}{punto}ilc_autorreconocimientoetnicotipo iae
           on iae.t_id = ii.grupo_etnico

    union all

    -- Camino 2: interesados que son miembros de una agrupación asociada al derecho.
    select
        pc.predio_id,
        pc.npn,
        pc.predio_tipo,
        'Agrupación'                  via,
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido,
                       ii.razon_social)  nombre,
        iae.ilicode                   grupo_etnico
    from cte_predios_colectivos pc
    join {esquema}{punto}ilc_derecho ide                 on ide.unidad = pc.predio_id
    join {esquema}{punto}col_rrrinteresado cri           on cri.rrr = ide.t_id
    join {esquema}{punto}cr_agrupacioninteresados cag
      on cag.t_id = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}col_miembros cm                 on cm.agrupacion = cag.t_id
    -- el rol "interesado" de col_miembros es polimórfico: la columna es
    -- interesado_ilc_interesado, no "interesado" (ver docs/02_modelo_juridico.md)
    join {esquema}{punto}ilc_interesado ii               on ii.t_id = cm.interesado_ilc_interesado
    left join {esquema}{punto}ilc_autorreconocimientoetnicotipo iae
           on iae.t_id = ii.grupo_etnico
)
, cte_validaciones as (
    select
        i.*,
        case when i.grupo_etnico is null or i.grupo_etnico = 'Ninguno'
             then 'Fail' else 'Ok' end  val_grupo_etnico
    from cte_interesados i
)
select distinct
    npn,
    predio_tipo,
    via,
    documento_identidad,
    nombre,
    grupo_etnico,
    'Fail' cond_2_26
from cte_validaciones
where val_grupo_etnico = 'Fail'
