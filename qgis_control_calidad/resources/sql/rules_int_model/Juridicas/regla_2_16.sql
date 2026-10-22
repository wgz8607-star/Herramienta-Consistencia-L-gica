-- =============================================================================
-- Regla 2.16 — Privado informal
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.16
-- Enunciado  : "Cuando el predio informal sea de tipo "Privado", el tipo de derecho
--              debe ser "Posesión"; si el predio cuenta con FMI el tipo de fuente
--              administrativa debe ser "Acto Administrativo", "Escritura", "Sentencia";
--              si el predio no cuenta con FMI el tipo de fuente administrativa debe ser
--              "Documento Privado" o "Sin Documento"."
-- Universo   : Predios tipo privado (hoja "Datos", id 27), en su parte informal.
--              informal = pos 22 in ('2','5') o condición 'Informal'; tipo = Predio.Privado.*
-- Falla si   : val_derecho — el tipo de derecho no es 'Posesion'.
--              val_fuente  — la fuente no corresponde al conjunto que exige la
--                            presencia o ausencia de FMI (ver `fuentes_esperadas`).
-- No aplica  : predios formales (2.15) o de otro tipo; predios con novedad de
--              cancelación.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              col_rrrfuente, ilc_fuenteadministrativa, col_fuenteadministrativatipo
-- Origen     : regla_2_2.sql (set anterior) — validaba solo que un informal no tuviera
--              FMI, criterio que el formato nuevo ya no sostiene.
-- Salida     : npn, formalidad, predio_tipo, derecho_tipo, fmi, tiene_fmi,
--              fuentes_esperadas, fuente_tipo, val_*, cond_2_16
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 2860 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- CAMBIO DE CRITERIO IMPORTANTE frente a regla_2_2:
--
--   regla_2_2 reportaba como error todo predio informal (Posesión u Ocupación) que
--   tuviera matrícula inmobiliaria — su comentario lo enunciaba como "un predio
--   informal no debe tener FMI".
--
--   El formato nuevo NO prohíbe el FMI en privados informales: lo admite y solo
--   cambia el conjunto de fuentes administrativas admisibles según lo tenga o no.
--   Un poseedor puede tener a la vista una escritura sin que el dominio esté
--   saneado, y eso es precisamente lo que el enunciado contempla.
--
--   Por eso aquí NO hay validación de FMI, solo de derecho y de fuente. Los predios
--   informales con FMI que regla_2_2 reportaba dejan de ser error.
--
-- La regla es condicional: `fuentes_esperadas` deja explícito en el reporte cuál era
-- el conjunto exigido en cada fila, para que el revisor no tenga que deducirlo.
-- =============================================================================

with cte_predios as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        'Informal'                    formalidad,
        ipt.ilicode                   predio_tipo,
        ip.matricula_inmobiliaria     fmi,
        coalesce(ip.matricula_inmobiliaria, 0) <> 0   tiene_fmi
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_prediotipo ipt on ipt.t_id = ip.tipo
    left join {esquema}{punto}ilc_condicionprediotipo icp on icp.t_id = ip.condicion_predio
    where ipt.ilicode like 'Predio.Privado.%'
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
        case when d.tiene_fmi
             then 'Acto Administrativo, Escritura o Sentencia'
             else 'Documento Privado o Sin Documento' end       fuentes_esperadas,
        case when coalesce(d.derecho_tipo, '') <> 'Posesion'
             then 'Fail' else 'Ok' end                          val_derecho,
        case
            -- con FMI: se exige documento fuente registrado
            when d.tiene_fmi
                 and coalesce(d.fuente_tipo, '') not in ('Documento_Fuente.Acto_Administrativo',
                                                         'Documento_Fuente.Escritura_Publica',
                                                         'Documento_Fuente.Sentencia_Judicial')
                 then 'Fail'
            -- sin FMI: documento privado o ninguno
            when not d.tiene_fmi
                 and coalesce(d.fuente_tipo, '') not in ('Documento_Fuente.Documento_Privado',
                                                         'Documento_Privado',
                                                         'Sin_Documento')
                 then 'Fail'
            else 'Ok'
        end                                                     val_fuente
    from cte_detalle d
)
select distinct
    npn, formalidad, predio_tipo, derecho_tipo, fmi, tiene_fmi,
    fuentes_esperadas, fuente_tipo,
    val_derecho, val_fuente,
    'Fail' cond_2_16
from cte_validaciones
where 'Fail' in (val_derecho, val_fuente)
