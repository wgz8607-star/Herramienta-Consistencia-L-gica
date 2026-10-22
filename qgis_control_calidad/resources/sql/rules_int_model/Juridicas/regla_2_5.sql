-- =============================================================================
-- Regla 2.5 — Uso Público formal SIN FMI
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.5
-- Enunciado  : "Cuando el predio formal sea de tipo "Uso Público" y no cuente con FMI;
--              el tipo de derecho debe ser "Dominio"; el interesado debe corresponder
--              a La Nación o al Municipio o a una EDP y el tipo de fuente
--              administrativa debe ser "Sin Documento"."
-- Universo   : Predios formales de uso público (hoja "Datos", id 85) sin FMI.
--              formal = no informal (ver 02_modelo_juridico.md); sin FMI = matricula_inmobiliaria nula o 0.
-- Falla si   : val_derecho    — el tipo de derecho no es 'Dominio'.
--              val_interesado — ningún interesado es La Nación, el Municipio ni una
--                               persona jurídica (aproximación de EDP).
--              val_fuente     — el tipo de fuente no es Sin_Documento.
-- No aplica  : predios informales (2.6), con FMI (2.4) o de otro tipo; predios con
--              novedad de cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              col_rrrinteresado, col_miembros, ilc_interesado, cr_interesadotipo,
--              col_rrrfuente, ilc_fuenteadministrativa, col_fuenteadministrativatipo
-- Origen     : NUEVA — el formato anterior no separaba con FMI / sin FMI.
-- Salida     : npn, formalidad, predio_tipo, derecho_tipo, fmi, razones_sociales,
--              fuente_tipo, val_*, cond_2_5
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 2 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Es la gemela de 2.4 para predios sin matrícula. La única diferencia sustantiva está
-- en la fuente administrativa: sin FMI no hay título registrado, así que el tipo de
-- fuente esperado es Sin_Documento y no un documento fuente.
--
-- Estos predios son además el supuesto de la regla 2.19, que exige que su fecha de
-- inicio de tenencia sea 1936-12-04 (rural) o 1959-12-31 (urbano). Las dos reglas se
-- complementan y se ejecutan sobre el mismo conjunto.
--
-- Aplica la misma limitación de EDP descrita en 2.4 (ver docs/03_hallazgos.md H-07).
-- =============================================================================

with cte_predios as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        'Formal'                      formalidad,
        ipt.ilicode                   predio_tipo,
        ip.matricula_inmobiliaria     fmi
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_prediotipo ipt on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_condicionprediotipo icp on icp.t_id = ip.condicion_predio
    where ipt.ilicode = 'Predio.Publico.Uso_Publico'
      and not (substring(ip.numero_predial_nacional, 22, 1) in ('2','5')
               or icp.ilicode = 'Informal')  -- formal
      and coalesce(ip.matricula_inmobiliaria, 0) = 0            -- sin FMI
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
        upper(translate(coalesce(ii.razon_social, ''),
                        'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'))  ent_norm,
        ii.razon_social,
        cit.ilicode  interesado_tipo
    from cte_predios p
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = p.predio_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cri.interesado_ilc_interesado
    left join {esquema}{punto}cr_interesadotipo cit on cit.t_id = ii.tipo

    union all

    select
        p.predio_id,
        upper(translate(coalesce(ii.razon_social, ''),
                        'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'))  ent_norm,
        ii.razon_social,
        cit.ilicode  interesado_tipo
    from cte_predios p
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = p.predio_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}col_miembros cm       on cm.agrupacion = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cm.interesado_ilc_interesado
    left join {esquema}{punto}cr_interesadotipo cit on cit.t_id = ii.tipo
)
, cte_interesado_predio as (
    select
        predio_id,
        bool_or(ent_norm ~ '\mNACION\M|\m(MUNICIPIO|ALCALDIA|DISTRITO)\M')  tiene_nacion_municipio,
        bool_or(interesado_tipo = 'Persona_Juridica')                       tiene_persona_juridica,
        string_agg(distinct nullif(trim(razon_social), ''), ' || ')         razones_sociales
    from cte_interesados
    group by predio_id
)
, cte_detalle as (
    select
        p.*,
        idt.ilicode                 derecho_tipo,
        cft.ilicode                 fuente_tipo,
        coalesce(ipx.tiene_nacion_municipio, false)  tiene_nacion_municipio,
        coalesce(ipx.tiene_persona_juridica, false)  tiene_persona_juridica,
        ipx.razones_sociales
    from cte_predios p
    left join cte_interesado_predio ipx on ipx.predio_id = p.predio_id
    left join {esquema}{punto}ilc_derecho ide              on ide.unidad = p.predio_id
    left join {esquema}{punto}ilc_derechocatastraltipo idt on idt.t_id = ide.tipo
    left join {esquema}{punto}col_rrrfuente crf            on crf.rrr = ide.t_id
    left join {esquema}{punto}ilc_fuenteadministrativa ifa on ifa.t_id = crf.fuente_administrativa
    left join {esquema}{punto}col_fuenteadministrativatipo cft on cft.t_id = ifa.tipo
)
, cte_validaciones as (
    select
        d.*,
        case when coalesce(d.derecho_tipo, '') <> 'Dominio'
             then 'Fail' else 'Ok' end                          val_derecho,
        case when not (d.tiene_nacion_municipio or d.tiene_persona_juridica)
             then 'Fail' else 'Ok' end                          val_interesado,
        case when coalesce(d.fuente_tipo, '') <> 'Sin_Documento'
             then 'Fail' else 'Ok' end                          val_fuente,
        case when not d.tiene_nacion_municipio and d.tiene_persona_juridica
             then 'Revisar contra listado EDP' else '' end      interesado_es_pj_generica
    from cte_detalle d
)
select distinct
    npn,
    formalidad,
    predio_tipo,
    derecho_tipo,
    fmi,
    razones_sociales,
    fuente_tipo,
    val_derecho,
    val_interesado,
    val_fuente,
    interesado_es_pj_generica,
    'Fail' cond_2_5
from cte_validaciones
where 'Fail' in (val_derecho, val_interesado, val_fuente)
