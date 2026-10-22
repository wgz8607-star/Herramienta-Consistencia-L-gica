-- =============================================================================
-- Regla 2.14 — Presunto Baldío informal SIN FMI
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.14
-- Enunciado  : "Cuando el predio informal sea de tipo "Presunto Baldío" y no cuente con
--              FMI; el tipo de derecho debe ser "Ocupación"; el interesado debe ser
--              diferente a La Nación o al Municipio y el tipo de fuente administrativa
--              debe ser "Documento Privado" o "Sin Documento"."
-- Universo   : Predios presunto baldío con derecho de ocupación (hoja "Datos", id 31),
--              en su parte informal sin FMI.
--              informal = pos 22 in ('2','5') o condición 'Informal'; sin FMI = matricula_inmobiliaria nula o 0.
-- Falla si   : val_derecho    — el tipo de derecho no es 'Ocupacion'.
--              val_interesado — algún interesado ES La Nación o el Municipio.
--              val_fuente     — el tipo de fuente no es Documento_Privado ni Sin_Documento.
-- No aplica  : predios formales (2.11, 2.12), con FMI (2.13) o de otro tipo;
--              predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              col_rrrinteresado, col_miembros, ilc_interesado, col_rrrfuente,
--              ilc_fuenteadministrativa, col_fuenteadministrativatipo
-- Origen     : regla_2_8.sql (set anterior)
-- Salida     : npn, zona, formalidad, predio_tipo, derecho_tipo, fmi,
--              razones_sociales, fuente_tipo, val_*, cond_2_14
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Es el caso más frecuente de presunto baldío: ocupación informal sin título. Se
-- diferencia de 2.13 únicamente en el conjunto de fuentes administrativas admisibles.
--
-- Se aplica la misma corrección del patrón de entidades que en 2.13 (ver H-13).
-- =============================================================================

with cte_predios as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        case when substring(ip.numero_predial_nacional, 6, 2) = '00'
             then 'Rural' else 'Urbano' end   zona,
        'Informal'                    formalidad,
        ipt.ilicode                   predio_tipo,
        ip.matricula_inmobiliaria     fmi
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_prediotipo ipt on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_condicionprediotipo icp on icp.t_id = ip.condicion_predio
    where ipt.ilicode = 'Predio.Publico.Presunto_Baldio'
      and (substring(ip.numero_predial_nacional, 22, 1) in ('2','5')
            or icp.ilicode = 'Informal')   -- informal
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
        ii.razon_social
    from cte_predios p
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = p.predio_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cri.interesado_ilc_interesado
    union all
    select
        p.predio_id,
        upper(translate(coalesce(ii.razon_social, ''),
                        'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'))  ent_norm,
        ii.razon_social
    from cte_predios p
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = p.predio_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}col_miembros cm       on cm.agrupacion = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}ilc_interesado ii     on ii.t_id = cm.interesado_ilc_interesado
)
, cte_interesado_predio as (
    select
        predio_id,
        bool_or(ent_norm ~ '\mNACION\M|\m(MUNICIPIO|ALCALDIA|DISTRITO)\M')  tiene_entidad,
        string_agg(distinct nullif(trim(razon_social), ''), ' || ')         razones_sociales
    from cte_interesados
    group by predio_id
)
, cte_detalle as (
    select
        p.*,
        idt.ilicode  derecho_tipo,
        cft.ilicode  fuente_tipo,
        coalesce(ipx.tiene_entidad, false)  tiene_entidad,
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
        case when coalesce(d.derecho_tipo, '') <> 'Ocupacion'
             then 'Fail' else 'Ok' end                          val_derecho,
        case when d.tiene_entidad
             then 'Fail' else 'Ok' end                          val_interesado,
        case when coalesce(d.fuente_tipo, '') not in ('Documento_Fuente.Documento_Privado',
                                                      'Documento_Privado',
                                                      'Sin_Documento')
             then 'Fail' else 'Ok' end                          val_fuente
    from cte_detalle d
)
select distinct
    npn, zona, formalidad, predio_tipo, derecho_tipo, fmi,
    razones_sociales, fuente_tipo,
    val_derecho, val_interesado, val_fuente,
    'Fail' cond_2_14
from cte_validaciones
where 'Fail' in (val_derecho, val_interesado, val_fuente)
