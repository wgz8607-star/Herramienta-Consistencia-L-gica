-- =============================================================================
-- Regla 2.12 — Presunto Baldío formal SIN FMI
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.12
-- Enunciado  : "Cuando el predio formal sea de tipo "Presunto Baldío" y no cuente con
--              FMI; el tipo de derecho debe ser "Dominio"; el interesado debe
--              corresponder a La Nación en zona rural o al Municipio en zona urbana y
--              el tipo de fuente administrativa debe ser "Sin Documento"."
-- Universo   : Predios tipo Predio.Publico.Presunto_Baldio, formales, sin FMI.
--              formal = no informal (ver 02_modelo_juridico.md); sin FMI = matricula_inmobiliaria nula o 0;
--              zona por NPN pos 6-7 ('00' rural, resto urbano).
-- Falla si   : val_derecho    — el tipo de derecho no es 'Dominio'.
--              val_interesado — en zona RURAL ningún interesado es La Nación;
--                               en zona URBANA ninguno es el Municipio.
--              val_fuente     — el tipo de fuente no es Sin_Documento.
-- No aplica  : predios informales (2.13, 2.14), con FMI (2.11) o de otro tipo;
--              predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              col_rrrinteresado, col_miembros, ilc_interesado, col_rrrfuente,
--              ilc_fuenteadministrativa, col_fuenteadministrativatipo
-- Origen     : regla_2_6.sql (set anterior)
-- Salida     : npn, zona, formalidad, predio_tipo, derecho_tipo, fmi,
--              interesado_esperado, razones_sociales, fuente_tipo, val_*, cond_2_12
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Diferencia clave con 2.11: aquí el interesado esperado DEPENDE DE LA ZONA. La Nación
-- en rural, el Municipio en urbano — no es indistinto como en 2.11. Es la única regla
-- del bloque A cuyo interesado esperado varía según la ubicación del predio, así que
-- la columna `interesado_esperado` explicita qué se esperaba en cada fila.
--
-- Estos predios son además el supuesto de la regla 2.19 (fecha de tenencia
-- 1936-12-04 rural / 1959-12-31 urbano). Las dos reglas se complementan.
-- =============================================================================

with cte_predios as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        case when substring(ip.numero_predial_nacional, 6, 2) = '00'
             then 'Rural' else 'Urbano' end   zona,
        'Formal'                      formalidad,
        ipt.ilicode                   predio_tipo,
        ip.matricula_inmobiliaria     fmi
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_prediotipo ipt on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_condicionprediotipo icp on icp.t_id = ip.condicion_predio
    where ipt.ilicode = 'Predio.Publico.Presunto_Baldio'
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
        -- se calculan por separado porque el esperado depende de la zona
        bool_or(ent_norm ~ '\mNACION\M')                             tiene_nacion,
        bool_or(ent_norm ~ '\m(MUNICIPIO|ALCALDIA|DISTRITO)\M')      tiene_municipio,
        string_agg(distinct nullif(trim(razon_social), ''), ' || ')  razones_sociales
    from cte_interesados
    group by predio_id
)
, cte_detalle as (
    select
        p.*,
        idt.ilicode  derecho_tipo,
        cft.ilicode  fuente_tipo,
        coalesce(ipx.tiene_nacion, false)     tiene_nacion,
        coalesce(ipx.tiene_municipio, false)  tiene_municipio,
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
        case when d.zona = 'Rural' then 'La Nación' else 'El Municipio' end  interesado_esperado,
        case when coalesce(d.derecho_tipo, '') <> 'Dominio'
             then 'Fail' else 'Ok' end                          val_derecho,
        case when (d.zona = 'Rural'  and not d.tiene_nacion)
               or (d.zona = 'Urbano' and not d.tiene_municipio)
             then 'Fail' else 'Ok' end                          val_interesado,
        case when coalesce(d.fuente_tipo, '') <> 'Sin_Documento'
             then 'Fail' else 'Ok' end                          val_fuente
    from cte_detalle d
)
select distinct
    npn, zona, formalidad, predio_tipo, derecho_tipo, fmi,
    interesado_esperado, razones_sociales, fuente_tipo,
    val_derecho, val_interesado, val_fuente,
    'Fail' cond_2_12
from cte_validaciones
where 'Fail' in (val_derecho, val_interesado, val_fuente)
