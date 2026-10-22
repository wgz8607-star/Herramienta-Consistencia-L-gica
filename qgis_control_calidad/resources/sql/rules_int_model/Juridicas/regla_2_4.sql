-- =============================================================================
-- Regla 2.4 — Uso Público formal CON FMI
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.4
-- Enunciado  : "Cuando el predio formal sea de tipo "Uso Público" y cuente con FMI; el
--              tipo de derecho debe ser "Dominio"; el interesado debe corresponder a
--              La Nación o al Municipio o a una EDP y el tipo de fuente administrativa
--              debe ser un "Acto Administrativo", "Escritura" o "Sentencia"."
-- Universo   : Predios formales de uso público (hoja "Datos", id 85) con FMI.
--              formal = no informal (ver 02_modelo_juridico.md); con FMI = matricula_inmobiliaria <> 0.
-- Falla si   : val_derecho    — el tipo de derecho no es 'Dominio'.
--              val_interesado — ningún interesado es La Nación, el Municipio ni una
--                               persona jurídica (aproximación de EDP — ver nota).
--              val_fuente     — el tipo de fuente no es Acto_Administrativo,
--                               Escritura_Publica ni Sentencia_Judicial.
-- No aplica  : predios informales (2.6), sin FMI (2.5) o de otro tipo; predios con
--              novedad de cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              col_rrrinteresado, col_miembros, ilc_interesado, cr_interesadotipo,
--              col_rrrfuente, ilc_fuenteadministrativa, col_fuenteadministrativatipo
-- Origen     : regla_2_9.sql (set anterior) — cubría solo "el interesado debe ser
--              Persona_Juridica", sin separar con FMI / sin FMI.
-- Salida     : npn, formalidad, predio_tipo, derecho_tipo, fmi, razones_sociales,
--              fuente_tipo, val_*, cond_2_4
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- LIMITACIÓN CONOCIDA — "EDP" (Entidad de Derecho Público) no está codificada en el
-- modelo: no hay atributo que la marque. El formato anota en la regla 2.8 que "se
-- genera el listado de los EDP para la marcación de excepciones", pero ese listado
-- todavía no está disponible.
--
-- Criterio aplicado mientras llega: se acepta el interesado si es La Nación, el
-- Municipio, o cualquier Persona_Juridica —que es lo mismo que hacía regla_2_9—.
-- Es una condición NECESARIA pero no suficiente: una persona jurídica privada pasaría
-- la validación. La columna `interesado_es_pj_generica` marca esos casos para que el
-- revisor los contraste contra el listado de EDP cuando exista.
-- Ver docs/03_hallazgos.md H-07.
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
      and coalesce(ip.matricula_inmobiliaria, 0) <> 0           -- con FMI
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
        -- La Nación o el Municipio, identificados por razón social
        bool_or(ent_norm ~ '\mNACION\M|\m(MUNICIPIO|ALCALDIA|DISTRITO)\M')  tiene_nacion_municipio,
        -- aproximación de EDP: cualquier persona jurídica
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
        case when coalesce(d.fuente_tipo, '') not in ('Documento_Fuente.Acto_Administrativo',
                                                      'Documento_Fuente.Escritura_Publica',
                                                      'Documento_Fuente.Sentencia_Judicial')
             then 'Fail' else 'Ok' end                          val_fuente,
        -- informativo: pasó por ser persona jurídica, sin poder confirmar que sea EDP
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
    'Fail' cond_2_4
from cte_validaciones
where 'Fail' in (val_derecho, val_interesado, val_fuente)
