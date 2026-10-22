-- =============================================================================
-- Regla 2.15 — Privado formal
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.15
-- Enunciado  : "Cuando el predio formal sea de tipo "Privado", el tipo de derecho debe
--              ser "Dominio"; el predio debe contar con FMI y el tipo de fuente
--              administrativa debe ser "Acto Administrativo", "Escritura" o "Sentencia"."
-- Universo   : Predios tipo privado (hoja "Datos", id 27), en su parte formal.
--              formal = no informal (ver 02_modelo_juridico.md); tipo = Predio.Privado.* (incluye
--              Privado.Privado y Privado.Colectivo).
-- Falla si   : val_derecho — el tipo de derecho no es 'Dominio'.
--              val_fmi     — el predio no tiene matrícula inmobiliaria.
--              val_fuente  — el tipo de fuente no es Acto_Administrativo,
--                            Escritura_Publica ni Sentencia_Judicial.
-- No aplica  : predios informales (2.16) o de otro tipo; predios con novedad de
--              cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              col_rrrfuente, ilc_fuenteadministrativa, col_fuenteadministrativatipo
-- Origen     : regla_2_2.sql (set anterior) — validaba solo la exigencia de FMI.
-- Salida     : npn, formalidad, predio_tipo, derecho_tipo, fmi, fuente_tipo,
--              numero_fuente, fecha_documento_fuente, val_*, cond_2_15
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 2 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Es la regla de mayor volumen del bloque A: el grueso del padrón catastral son
-- predios privados formales. Conviene revisar primero sus conteos para calibrar si
-- los criterios producen un número de errores plausible.
--
-- Se usa `like 'Predio.Privado.%'` en vez de listar los subtipos, para cubrir tanto
-- Privado.Privado como Privado.Colectivo y no romperse si se agrega uno nuevo.
--
-- CORRECCIÓN heredada de regla_2_2: la condición de FMI era
-- `ip.matricula_inmobiliaria is null`, que deja pasar los predios con matrícula = 0.
-- Además regla_2_2 no incluía Privado.Colectivo en su lista de tipos, así que los
-- predios colectivos formales nunca se validaban.
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
    where ipt.ilicode like 'Predio.Privado.%'
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
, cte_detalle as (
    select
        p.*,
        idt.ilicode  derecho_tipo,
        cft.ilicode  fuente_tipo,
        ifa.numero_fuente,
        ifa.fecha_documento_fuente
    from cte_predios p
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
        case when coalesce(d.fuente_tipo, '') not in ('Documento_Fuente.Acto_Administrativo',
                                                      'Documento_Fuente.Escritura_Publica',
                                                      'Documento_Fuente.Sentencia_Judicial')
             then 'Fail' else 'Ok' end                          val_fuente
    from cte_detalle d
)
select distinct
    npn, formalidad, predio_tipo, derecho_tipo, fmi,
    fuente_tipo, numero_fuente, fecha_documento_fuente,
    val_derecho, val_fmi, val_fuente,
    'Fail' cond_2_15
from cte_validaciones
where 'Fail' in (val_derecho, val_fmi, val_fuente)
