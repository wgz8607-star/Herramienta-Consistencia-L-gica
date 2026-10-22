-- =============================================================================
-- Regla 2.9 — Fiscal Patrimonial informal: derecho, FMI y fuente
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.9
-- Enunciado  : "Cuando el predio informal sea de tipo "Fiscal Patrimonial", el tipo de
--              derecho debe ser "Ocupacíón"; el predio no debe contar con FMI y el tipo
--              de fuente administrativa debe ser "Documento Privado" o "Sin Documento"."
--              (el formato escribe "Ocupacíón" con errata; el ilicode es 'Ocupacion')
-- Universo   : Predios de tipo Fiscal_Patrimonial informales (pos22 in ('2','5') o condición 'Informal').
-- Falla si   : val_derecho — el tipo de derecho no es 'Ocupacion'.
--              val_sin_fmi — el predio tiene matrícula inmobiliaria.
--              val_fuente  — el tipo de fuente no es Documento_Privado ni Sin_Documento.
-- No aplica  : predios formales (2.7 y 2.8) o de otro tipo; predios con novedad de
--              cancelación. El requisito sobre el interesado lo valida la regla 2.10.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              col_rrrfuente, ilc_fuenteadministrativa, col_fuenteadministrativatipo
-- Origen     : NUEVA — el formato anterior no tenía equivalente.
-- Salida     : npn, formalidad, predio_tipo, derecho_tipo, fmi, fuente_tipo,
--              val_*, cond_2_9
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 157 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Espejo informal de la regla 2.7. Un fiscal patrimonial ocupado informalmente no
-- tiene título registrado, de ahí que no deba contar con FMI y que la fuente
-- administrativa admisible sea documento privado o ninguna.
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
, cte_detalle as (
    select
        p.*,
        idt.ilicode  derecho_tipo,
        cft.ilicode  fuente_tipo
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
        case when coalesce(d.derecho_tipo, '') <> 'Ocupacion'
             then 'Fail' else 'Ok' end                          val_derecho,
        case when coalesce(d.fmi, 0) <> 0
             then 'Fail' else 'Ok' end                          val_sin_fmi,
        case when coalesce(d.fuente_tipo, '') not in ('Documento_Fuente.Documento_Privado',
                                                      'Documento_Privado',
                                                      'Sin_Documento')
             then 'Fail' else 'Ok' end                          val_fuente
    from cte_detalle d
)
select distinct
    npn,
    formalidad,
    predio_tipo,
    derecho_tipo,
    fmi,
    fuente_tipo,
    val_derecho,
    val_sin_fmi,
    val_fuente,
    'Fail' cond_2_9
from cte_validaciones
where 'Fail' in (val_derecho, val_sin_fmi, val_fuente)
