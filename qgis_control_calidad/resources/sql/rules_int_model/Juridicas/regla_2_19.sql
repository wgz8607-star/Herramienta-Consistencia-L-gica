-- =============================================================================
-- Regla 2.19 — Fechas normativas de tenencia para Dominio sin FMI
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.19
-- Enunciado  : "Si el derecho es de tipo "Dominio", el tipo de predio es "Uso Público"
--              o "Presunto Baldío" y el predio no cuenta con FMI, la fecha de inicio
--              de la tenencia debe ser 04/12/1936 para predios en zona rural o
--              31/12/1959 para predios en zona urbana."
-- Universo   : Total de derechos (hoja "Datos", id 24), restringido a
--              Dominio + tipo Uso_Publico o Presunto_Baldio + sin FMI.
-- Falla si   : val_fecha — predio rural  (NPN pos 6-7 = '00') y fecha <> 1936-12-04
--              val_fecha — predio urbano (NPN pos 6-7 <> '00') y fecha <> 1959-12-31
--              (una fecha nula también falla)
-- No aplica  : predios con novedad de cancelación; predios con FMI; tipos de predio
--              distintos de Uso_Publico y Presunto_Baldio.
-- Tablas     : ilc_predio, ilc_prediotipo, ilc_derecho, ilc_derechocatastraltipo,
--              ilc_datosadicionaleslevantamientocatastral,
--              ilc_estructuranovedadnumeropredial(+_tipo_novedad)
-- Origen     : regla_2_1.sql (set anterior) — la excepción se convierte en regla propia.
-- Salida     : npn, zona, predio_tipo, fecha_inicio_tenencia, fecha_esperada, cond_2_19
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 201 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Fundamento de las fechas:
--   1936-12-04 → Ley 200 de 1936 (régimen de tierras, zona rural)
--   1959-12-31 → corte adoptado para predios urbanos
-- Cambio frente al set anterior: regla_2_1 aplicaba la excepción a CUALQUIER predio
-- con Dominio sin FMI. El formato nuevo la restringe a Uso_Publico y Presunto_Baldio.
-- Un predio Privado con Dominio y sin FMI ya no debe evaluarse aquí — ese caso lo
-- cubre la regla 2.15, que exige que un privado formal tenga FMI.
-- =============================================================================

with cte_base as (
    select
        ip.numero_predial_nacional     npn,
        -- posiciones 6-7 del NPN: '00' = rural, '01'..'99' = urbano
        substring(ip.numero_predial_nacional, 6, 2)  sector,
        case when substring(ip.numero_predial_nacional, 6, 2) = '00'
             then 'Rural' else 'Urbano' end          zona,
        ipt.ilicode                    predio_tipo,
        idt.ilicode                    derecho_tipo,
        ip.matricula_inmobiliaria      fmi,
        ide.fecha_inicio_tenencia      fecha_inicio_tenencia
    from {esquema}{punto}ilc_predio ip
    join      {esquema}{punto}ilc_derecho ide              on ide.unidad = ip.t_id
    left join {esquema}{punto}ilc_derechocatastraltipo idt on idt.t_id = ide.tipo
    left join {esquema}{punto}ilc_prediotipo ipt           on ipt.t_id = ip.tipo
    where idt.ilicode = 'Dominio'
      and ipt.ilicode in ('Predio.Publico.Uso_Publico',
                          'Predio.Publico.Presunto_Baldio')
      -- "no cuenta con FMI": nulo o cero. El set anterior comparaba contra el
      -- literal '0' (cast implícito); coalesce es explícito y no depende del tipo.
      and coalesce(ip.matricula_inmobiliaria, 0) = 0
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
, cte_validaciones as (
    select
        b.*,
        case when b.zona = 'Rural' then date '1936-12-04'
                                   else date '1959-12-31' end  fecha_esperada
    from cte_base b
)
select distinct
    npn,
    zona,
    predio_tipo,
    fmi,
    fecha_inicio_tenencia,
    fecha_esperada,
    'Fail' cond_2_19
from cte_validaciones
-- IS DISTINCT FROM captura también el caso de fecha nula
where fecha_inicio_tenencia is distinct from fecha_esperada
