-- =============================================================================
-- Regla 2.2 — Baldío rural formal
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.2
-- Enunciado  : "Cuando el predio este ubicado en zona rural y sea un predio formal de
--              tipo "Baldío", el tipo de derecho debe ser "Dominio"; el predio debe
--              contar con FMI; el interesado debe ser La Nación, INCORA, INCODER, o
--              ANT; el tipo de fuente administrativa debe ser "Acto Administrativo" y
--              el ente emisor debe estar registrado."
-- Universo   : Predios rurales, formales y baldíos (hoja "Datos", id 83).
--              zona rural = NPN pos 6-7 = '00'; formal = no informal (ver 02_modelo_juridico.md);
--              tipo = Predio.Publico.Baldio.Baldio o .Reserva_Indigena
-- Falla si   : val_derecho   — el tipo de derecho no es 'Dominio'.
--              val_fmi       — el predio no tiene matrícula inmobiliaria.
--              val_interesado— ningún interesado del predio es Nación, INCORA,
--                              INCODER ni ANT.
--              val_fuente    — el tipo de fuente no es Acto_Administrativo.
--              val_ente      — el ente emisor no está diligenciado.
-- No aplica  : predios urbanos, informales o de otro tipo; predios con novedad de
--              cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              col_rrrinteresado, col_miembros, ilc_interesado, col_rrrfuente,
--              ilc_fuenteadministrativa, col_fuenteadministrativatipo
-- Origen     : regla_2_6.sql (set anterior) — cubría solo la parte de interesado.
-- Salida     : npn, zona, formalidad, predio_tipo, derecho_tipo, fmi, razones_sociales,
--              fuente_tipo, ente_emisor, val_*, cond_2_2
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 1107 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- El enunciado nuevo encadena CINCO condiciones; regla_2_6 solo validaba el
-- interesado, y lo hacía junto con Presunto_Baldío en la misma consulta. Aquí se
-- descompone en val_* independientes para que el reporte diga cuál falló.
--
-- El interesado se evalúa POR PREDIO, no por fila: un predio puede tener varios
-- interesados y basta con que uno sea la entidad esperada. Evaluarlo fila a fila
-- —como hacía regla_2_6— reporta como error a los copropietarios que acompañan a
-- la entidad.
--
-- CORRECCIÓN: regla_2_6 usaba `razon_social not ilike '%ant%'`, que coincide con
-- SANTANDER, GARANTÍAS, ADELANTE. Se usa el patrón compartido con límites de palabra
-- documentado en docs/02_modelo_juridico.md. Ver hallazgo H-13.
-- =============================================================================

with cte_predios as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        case when substring(ip.numero_predial_nacional, 6, 2) = '00'
             then 'Rural' else 'Urbano' end            zona,
        'Formal'                      formalidad,
        ipt.ilicode                   predio_tipo,
        ip.matricula_inmobiliaria     fmi
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_prediotipo ipt on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_condicionprediotipo icp on icp.t_id = ip.condicion_predio
    where ipt.ilicode like 'Predio.Publico.Baldio%'
      -- zona rural
      and substring(ip.numero_predial_nacional, 6, 2) = '00'
      -- predio formal (criterio del bloque A, ver docs/02_modelo_juridico.md)
      and not (substring(ip.numero_predial_nacional, 22, 1) in ('2','5')
               or icp.ilicode = 'Informal')
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
    -- Interesados del predio por las dos vías (individual y por agrupación),
    -- con la razón social normalizada para el patrón de entidades.
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
    -- Un registro por predio: ¿alguno de sus interesados es la entidad esperada?
    select
        predio_id,
        bool_or(ent_norm ~ '\mNACION\M|\mANT\M|AGENCIA NACIONAL DE TIERRAS|\mINCORA\M|\mINCODER\M|INSTITUTO COLOMBIANO DE (LA )?REFORMA AGRARIA|INSTITUTO COLOMBIANO DE DESARROLLO RURAL')
                                                              tiene_entidad,
        string_agg(distinct nullif(trim(razon_social), ''), ' || ')  razones_sociales
    from cte_interesados
    group by predio_id
)
, cte_detalle as (
    select
        p.*,
        idt.ilicode                 derecho_tipo,
        cft.ilicode                 fuente_tipo,
        ifa.ente_emisor             ente_emisor,
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
        case when coalesce(d.derecho_tipo, '') <> 'Dominio'
             then 'Fail' else 'Ok' end                          val_derecho,
        case when coalesce(d.fmi, 0) = 0
             then 'Fail' else 'Ok' end                          val_fmi,
        case when not d.tiene_entidad
             then 'Fail' else 'Ok' end                          val_interesado,
        case when coalesce(d.fuente_tipo, '') <> 'Documento_Fuente.Acto_Administrativo'
             then 'Fail' else 'Ok' end                          val_fuente,
        case when coalesce(trim(d.ente_emisor), '') = ''
             then 'Fail' else 'Ok' end                          val_ente
    from cte_detalle d
)
select distinct
    npn,
    zona,
    formalidad,
    predio_tipo,
    derecho_tipo,
    fmi,
    razones_sociales,
    fuente_tipo,
    ente_emisor,
    val_derecho,
    val_fmi,
    val_interesado,
    val_fuente,
    val_ente,
    'Fail' cond_2_2
from cte_validaciones
where 'Fail' in (val_derecho, val_fmi, val_interesado, val_fuente, val_ente)
