-- =============================================================================
-- Regla 2.8 — Fiscal Patrimonial formal: el interesado debe ser una EDP
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.8
-- Enunciado  : "Cuando el predio formal sea de tipo "Fiscal Patrimonial" el interesado
--              debe ser una Persona Jurídica y debe corresponder a una Entidad de
--              Derecho Público (EDP). Nota: Se genera el listado de los EDP para la
--              marcación de excepciones."
-- Universo   : Públicos fiscales patrimoniales con derecho de dominio (hoja "Datos",
--              id 32), en su parte formal.
-- Falla si   : val_existe_interesado — el predio no tiene ningún interesado.
--              val_persona_juridica  — algún interesado del predio NO es
--                                      Persona_Juridica.
-- No aplica  : predios informales (2.10) o de otro tipo; predios con novedad de
--              cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, col_rrrinteresado,
--              col_miembros, ilc_interesado, cr_interesadotipo
-- Origen     : regla_2_9.sql (set anterior)
-- Salida     : npn, predio_tipo, n_interesados, n_naturales, razones_sociales,
--              val_*, cond_2_8
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 1 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- LIMITACIÓN CONOCIDA — la parte "debe corresponder a una EDP" NO es automatizable
-- con el modelo actual: no existe atributo que marque a un interesado como Entidad de
-- Derecho Público. El propio formato lo reconoce y anuncia un listado externo que
-- todavía no está disponible.
--
-- Lo que esta regla valida es la parte verificable: que TODOS los interesados del
-- predio sean Persona_Juridica. Es condición necesaria pero no suficiente.
-- La columna `razones_sociales` se incluye precisamente para que el revisor pueda
-- contrastar manualmente contra el listado de EDP cuando exista.
-- Ver docs/03_hallazgos.md H-07. Solicitar el listado al área funcional.
--
-- Cambios frente a regla_2_9:
--   * regla_2_9 evaluaba fila a fila con `ci.ilicode <> 'Persona_Juridica'`. Con
--     LEFT JOIN, un interesado sin tipo asignado daba NULL y no se reportaba.
--     Se cuenta por predio y se compara con coalesce.
--   * regla_2_9 mezclaba Fiscal_Patrimonial con Uso_Publico en la misma consulta;
--     el formato nuevo los separa (Uso_Publico pasa a 2.4 y 2.5).
--   * regla_2_9 ignoraba los interesados dentro de agrupaciones.
-- =============================================================================

with cte_predios as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        'Formal'                      formalidad,
        ipt.ilicode                   predio_tipo
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_prediotipo ipt on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_condicionprediotipo icp on icp.t_id = ip.condicion_predio
    where ipt.ilicode = 'Predio.Publico.Fiscal_Patrimonial'
      and not (substring(ip.numero_predial_nacional, 22, 1) in ('2','5')
               or icp.ilicode = 'Informal')  -- formal
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
    select
        p.predio_id,
        ii.t_id       interesado_id,
        ii.razon_social,
        cit.ilicode   interesado_tipo
    from cte_predios p
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = p.predio_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cri.interesado_ilc_interesado
    left join {esquema}{punto}cr_interesadotipo cit on cit.t_id = ii.tipo

    union

    select
        p.predio_id,
        ii.t_id       interesado_id,
        ii.razon_social,
        cit.ilicode   interesado_tipo
    from cte_predios p
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = p.predio_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}col_miembros cm       on cm.agrupacion = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cm.interesado_ilc_interesado
    left join {esquema}{punto}cr_interesadotipo cit on cit.t_id = ii.tipo
)
, cte_conteos as (
    select
        p.predio_id,
        p.npn,
        p.predio_tipo,
        count(i.interesado_id)                                                n_interesados,
        count(*) filter (where coalesce(i.interesado_tipo, '') <> 'Persona_Juridica'
                           and i.interesado_id is not null)                   n_no_juridicas,
        string_agg(distinct nullif(trim(i.razon_social), ''), ' || ')          razones_sociales
    from cte_predios p
    left join cte_interesados i on i.predio_id = p.predio_id
    group by p.predio_id, p.npn, p.predio_tipo
)
, cte_validaciones as (
    select
        c.*,
        case when c.n_interesados = 0 then 'Fail' else 'Ok' end   val_existe_interesado,
        case when c.n_no_juridicas > 0 then 'Fail' else 'Ok' end  val_persona_juridica
    from cte_conteos c
)
select
    npn,
    predio_tipo,
    n_interesados,
    n_no_juridicas,
    razones_sociales,
    val_existe_interesado,
    val_persona_juridica,
    'Revisar contra listado EDP'  nota_edp,
    'Fail' cond_2_8
from cte_validaciones
where 'Fail' in (val_existe_interesado, val_persona_juridica)
