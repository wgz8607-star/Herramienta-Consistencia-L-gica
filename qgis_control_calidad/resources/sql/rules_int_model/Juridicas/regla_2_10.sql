-- =============================================================================
-- Regla 2.10 — Fiscal Patrimonial informal: interesado distinto al titular formal
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.10
-- Enunciado  : "Cuando el predio informal sea de tipo "Fiscal Patrimonial" el
--              interesado debe ser diferente a quien ostenta el derecho de dominio del
--              predio formal asociado."
-- Universo   : Predios de tipo Fiscal_Patrimonial informales (pos22 in ('2','5') o condición 'Informal') con
--              predio formal asociado en ilc_predio_informalidad.
-- Falla si   : val_interesado — algún interesado del informal coincide (por documento
--              de identidad) con el titular de DOMINIO del predio formal asociado.
-- No aplica  : predios formales (2.8) o de otro tipo; predios informales sin relación
--              registrada en ilc_predio_informalidad; predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_predio_informalidad, ilc_derecho,
--              ilc_derechocatastraltipo, col_rrrinteresado, col_miembros, ilc_interesado
-- Origen     : regla_2_35.sql (set anterior)
-- Salida     : npn, npn_formal, documento_coincidente, nombre_coincidente, cond_2_10
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Misma lógica que la regla 2.6, aplicada a Fiscal_Patrimonial en lugar de
-- Uso_Publico. Ambas derivan de regla_2_35, que hacía la comparación sin restringir
-- el tipo de predio ni el tipo de derecho del formal. Ver docs/03_hallazgos.md H-09.
--
-- Cambios frente a regla_2_35:
--   * Se filtra el derecho del predio formal a 'Dominio': el enunciado habla de "quien
--     ostenta el derecho de dominio", no de cualquier interesado del formal.
--   * Se recorren las dos vías de interesado (individual y por agrupación) en ambos
--     lados de la comparación; regla_2_35 solo miraba los individuales.
--   * Se reporta el nombre además del documento, para que el revisor identifique a la
--     persona sin volver a la base.
-- =============================================================================

with cte_predios as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        ipt.ilicode                   predio_tipo
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_prediotipo ipt on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_condicionprediotipo icp on icp.t_id = ip.condicion_predio
    where ipt.ilicode = 'Predio.Publico.Fiscal_Patrimonial'
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
    select
        p.predio_id,
        p.npn,
        trim(ii.documento_identidad)  documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido,
                       ii.razon_social)  nombre
    from cte_predios p
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = p.predio_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cri.interesado_ilc_interesado
    where coalesce(trim(ii.documento_identidad), '') <> ''
    union
    select
        p.predio_id,
        p.npn,
        trim(ii.documento_identidad)  documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido,
                       ii.razon_social)  nombre
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
        ipi.igc_predio_informal     predio_id,
        pf.numero_predial_nacional  npn_formal,
        trim(ii.documento_identidad) documento_identidad
    from cte_predios p
    join {esquema}{punto}ilc_predio_informalidad ipi   on ipi.igc_predio_informal = p.predio_id
    join {esquema}{punto}ilc_predio pf                 on pf.t_id = ipi.igc_predio_formal
    join {esquema}{punto}ilc_derecho idf               on idf.unidad = pf.t_id
    join {esquema}{punto}ilc_derechocatastraltipo idtf on idtf.t_id = idf.tipo
    join {esquema}{punto}col_rrrinteresado crif        on crif.rrr = idf.t_id
    join {esquema}{punto}ilc_interesado ii             on ii.t_id = crif.interesado_ilc_interesado
    where idtf.ilicode = 'Dominio'
      and coalesce(trim(ii.documento_identidad), '') <> ''
    union
    select
        ipi.igc_predio_informal     predio_id,
        pf.numero_predial_nacional  npn_formal,
        trim(ii.documento_identidad) documento_identidad
    from cte_predios p
    join {esquema}{punto}ilc_predio_informalidad ipi   on ipi.igc_predio_informal = p.predio_id
    join {esquema}{punto}ilc_predio pf                 on pf.t_id = ipi.igc_predio_formal
    join {esquema}{punto}ilc_derecho idf               on idf.unidad = pf.t_id
    join {esquema}{punto}ilc_derechocatastraltipo idtf on idtf.t_id = idf.tipo
    join {esquema}{punto}col_rrrinteresado crif        on crif.rrr = idf.t_id
    join {esquema}{punto}col_miembros cmf              on cmf.agrupacion = crif.interesado_cr_agrupacioninteresados
    join {esquema}{punto}ilc_interesado ii             on ii.t_id = cmf.interesado_ilc_interesado
    where idtf.ilicode = 'Dominio'
      and coalesce(trim(ii.documento_identidad), '') <> ''
)
select distinct
    i.npn,
    f.npn_formal,
    i.documento_identidad  documento_coincidente,
    i.nombre               nombre_coincidente,
    'Fail' cond_2_10
from cte_int_informal i
join cte_int_formal f
  on f.predio_id = i.predio_id
 and f.documento_identidad = i.documento_identidad
