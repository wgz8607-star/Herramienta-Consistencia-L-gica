-- =============================================================================
-- Regla 2.6 — Uso Público informal
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.6
-- Enunciado  : "Cuando el predio informal sea de tipo "Uso Público", el tipo de derecho
--              debe ser "Ocupación"; el predio no debe contar con FMI; el interesado
--              debe ser diferente a quien ostenta el derecho de dominio del predio
--              formal asociado y el tipo de fuente administrativa debe corresponder a
--              "Documento Privado" o "Sin Documento"."
-- Universo   : Predios de tipo Uso_Publico informales (pos22 in ('2','5') o condición 'Informal').
-- Falla si   : val_derecho    — el tipo de derecho no es 'Ocupacion'.
--              val_sin_fmi    — el predio tiene matrícula inmobiliaria.
--              val_interesado — algún interesado del informal coincide (por documento
--                               de identidad) con el titular de DOMINIO del predio
--                               formal asociado vía ilc_predio_informalidad.
--              val_fuente     — el tipo de fuente no es Documento_Privado ni Sin_Documento.
-- No aplica  : predios formales (2.4 y 2.5) o de otro tipo; predios con novedad de
--              cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              ilc_predio_informalidad, col_rrrinteresado, col_miembros,
--              ilc_interesado, col_rrrfuente, ilc_fuenteadministrativa,
--              col_fuenteadministrativatipo
-- Origen     : regla_2_35.sql (set anterior) — cubría solo la comparación de
--              interesados, sin restringir a Uso_Publico ni validar derecho/FMI/fuente.
-- Salida     : npn, npn_formal, predio_tipo, derecho_tipo, fmi, documento_coincidente,
--              fuente_tipo, val_*, cond_2_6
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambios frente a regla_2_35 (ver docs/03_hallazgos.md H-09):
--   * regla_2_35 clasificaba formal/informal por pos 22, igual que aquí, pero NO
--     filtraba el derecho del predio formal. El enunciado habla de "quien ostenta el
--     derecho de DOMINIO del predio formal": si el formal tiene además un poseedor,
--     compararse con él no es lo que se pide. Aquí se filtra a Dominio.
--   * regla_2_35 solo miraba interesados individuales
--     (cri.interesado_ilc_interesado) e ignoraba los que están dentro de una
--     agrupación. Aquí se recorren las dos vías en ambos lados de la comparación.
--
-- DECISIÓN PENDIENTE: un predio informal SIN registro en ilc_predio_informalidad no
-- tiene formal asociado, así que val_interesado no puede evaluarse y queda en 'Ok'.
-- Que falte esa relación es un defecto en sí mismo, pero corresponde al componente
-- administrativo (regla 1.51 cuenta los registros de ilc_predio_informalidad), no a
-- esta regla. Se expone en la columna `tiene_formal_asociado` para que sea visible.
-- =============================================================================

with cte_predios as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        'Informal'                    formalidad,
        ipt.ilicode                   predio_tipo,
        ip.matricula_inmobiliaria     fmi
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_prediotipo ipt on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_condicionprediotipo icp on icp.t_id = ip.condicion_predio
    where ipt.ilicode = 'Predio.Publico.Uso_Publico'
      and (substring(ip.numero_predial_nacional, 22, 1) in ('2','5')
            or icp.ilicode = 'Informal')   -- informal
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
-- Interesados del predio INFORMAL (ambas vías)
, cte_int_informal as (
    select p.predio_id, ii.documento_identidad
    from cte_predios p
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = p.predio_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cri.interesado_ilc_interesado
    where coalesce(trim(ii.documento_identidad), '') <> ''
    union
    select p.predio_id, ii.documento_identidad
    from cte_predios p
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = p.predio_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}col_miembros cm       on cm.agrupacion = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cm.interesado_ilc_interesado
    where coalesce(trim(ii.documento_identidad), '') <> ''
)
-- Titulares de DOMINIO del predio formal asociado (ambas vías)
, cte_int_formal as (
    select
        ipi.igc_predio_informal   predio_id,
        pf.numero_predial_nacional npn_formal,
        ii.documento_identidad
    from cte_predios p
    join {esquema}{punto}ilc_predio_informalidad ipi on ipi.igc_predio_informal = p.predio_id
    join {esquema}{punto}ilc_predio pf               on pf.t_id = ipi.igc_predio_formal
    join {esquema}{punto}ilc_derecho idf             on idf.unidad = pf.t_id
    join {esquema}{punto}ilc_derechocatastraltipo idtf on idtf.t_id = idf.tipo
    join {esquema}{punto}col_rrrinteresado crif      on crif.rrr = idf.t_id
    join {esquema}{punto}ilc_interesado ii           on ii.t_id = crif.interesado_ilc_interesado
    where idtf.ilicode = 'Dominio'
      and coalesce(trim(ii.documento_identidad), '') <> ''
    union
    select
        ipi.igc_predio_informal   predio_id,
        pf.numero_predial_nacional npn_formal,
        ii.documento_identidad
    from cte_predios p
    join {esquema}{punto}ilc_predio_informalidad ipi on ipi.igc_predio_informal = p.predio_id
    join {esquema}{punto}ilc_predio pf               on pf.t_id = ipi.igc_predio_formal
    join {esquema}{punto}ilc_derecho idf             on idf.unidad = pf.t_id
    join {esquema}{punto}ilc_derechocatastraltipo idtf on idtf.t_id = idf.tipo
    join {esquema}{punto}col_rrrinteresado crif      on crif.rrr = idf.t_id
    join {esquema}{punto}col_miembros cmf            on cmf.agrupacion = crif.interesado_cr_agrupacioninteresados
    join {esquema}{punto}ilc_interesado ii           on ii.t_id = cmf.interesado_ilc_interesado
    where idtf.ilicode = 'Dominio'
      and coalesce(trim(ii.documento_identidad), '') <> ''
)
-- ¿Coincide algún documento entre informal y formal?
, cte_coincidencias as (
    select
        f.predio_id,
        max(f.npn_formal)                                        npn_formal,
        string_agg(distinct i.documento_identidad, ', ')          documento_coincidente
    from cte_int_formal f
    join cte_int_informal i
      on i.predio_id = f.predio_id
     and trim(i.documento_identidad) = trim(f.documento_identidad)
    group by f.predio_id
)
, cte_detalle as (
    select
        p.*,
        idt.ilicode                 derecho_tipo,
        cft.ilicode                 fuente_tipo,
        c.npn_formal,
        c.documento_coincidente,
        exists (select 1 from {esquema}{punto}ilc_predio_informalidad ipi2
                 where ipi2.igc_predio_informal = p.predio_id)  tiene_formal_asociado
    from cte_predios p
    left join cte_coincidencias c on c.predio_id = p.predio_id
    left join {esquema}{punto}ilc_derecho ide              on ide.unidad = p.predio_id
    left join {esquema}{punto}ilc_derechocatastraltipo idt on idt.t_id = ide.tipo
    left join {esquema}{punto}col_rrrfuente crf            on crf.rrr = ide.t_id
    left join {esquema}{punto}ilc_fuenteadministrativa ifa on ifa.t_id = crf.fuente_administrativa
    left join {esquema}{punto}col_fuenteadministrativatipo cft on cft.t_id = ifa.tipo
)
, cte_validaciones as (
    select
        d.*,
        case when coalesce(d.derecho_tipo, '') <> 'Ocupacion'
             then 'Fail' else 'Ok' end                          val_derecho,
        case when coalesce(d.fmi, 0) <> 0
             then 'Fail' else 'Ok' end                          val_sin_fmi,
        -- condición NEGATIVA: coincidir con el titular del formal es el error
        case when d.documento_coincidente is not null
             then 'Fail' else 'Ok' end                          val_interesado,
        case when coalesce(d.fuente_tipo, '') not in ('Documento_Fuente.Documento_Privado',
                                                      'Documento_Privado',
                                                      'Sin_Documento')
             then 'Fail' else 'Ok' end                          val_fuente
    from cte_detalle d
)
select distinct
    npn,
    npn_formal,
    tiene_formal_asociado,
    predio_tipo,
    derecho_tipo,
    fmi,
    documento_coincidente,
    fuente_tipo,
    val_derecho,
    val_sin_fmi,
    val_interesado,
    val_fuente,
    'Fail' cond_2_6
from cte_validaciones
where 'Fail' in (val_derecho, val_sin_fmi, val_interesado, val_fuente)
