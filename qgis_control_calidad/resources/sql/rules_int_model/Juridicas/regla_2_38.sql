-- =============================================================================
-- Regla 2.38 — Agrupación solo de personas jurídicas ⇒ Grupo_Empresarial
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.38
-- Enunciado  : "Cuando la agrupación de interesados de un predio esté conformada
--              únicamente por personas jurídicas, el tipo de agrupación debe ser
--              "Grupo_Empresarial"."
-- Universo   : Agrupaciones de interesados conformadas solo por personas jurídicas
--              (hoja "Datos", id 38).
-- Falla si   : el tipo de agrupación no es 'Grupo_Empresarial' (incluye el tipo nulo).
-- No aplica  : agrupaciones mixtas (2.36) o solo naturales (2.37); predios con
--              novedad de cancelación.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, cr_agrupacioninteresados,
--              col_miembros, ilc_interesado, cr_interesadotipo, col_grupointeresadotipo
-- Origen     : regla_2_25.sql (set anterior)
-- Salida     : npn, agrupacion_id, nombre_agrupacion, n_naturales, n_juridicas,
--              tipo_agrupacion, cond_2_38
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Mismo cambio de fondo que 2.36 y 2.37: regla_2_25 agrupaba por PREDIO en vez de
-- por AGRUPACIÓN, fusionando agrupaciones distintas del mismo predio y produciendo
-- conteos que no correspondían a ninguna agrupación real.
-- =============================================================================

with cte_agrupaciones as (
    select
        ip.numero_predial_nacional    npn,
        cag.t_id                      agrupacion_id,
        cag.nombre                    nombre_agrupacion,
        cgt.ilicode                   tipo_agrupacion,
        cit.ilicode                   interesado_tipo
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide          on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrinteresado cri    on cri.rrr = ide.t_id
    join {esquema}{punto}cr_agrupacioninteresados cag
      on cag.t_id = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}col_miembros cm          on cm.agrupacion = cag.t_id
    join {esquema}{punto}ilc_interesado ii        on ii.t_id = cm.interesado_ilc_interesado
    left join {esquema}{punto}cr_interesadotipo cit        on cit.t_id = ii.tipo
    left join {esquema}{punto}col_grupointeresadotipo cgt  on cgt.t_id = cag.tipo
    where not exists (
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
, cte_conteos as (
    select
        npn,
        agrupacion_id,
        max(nombre_agrupacion)  nombre_agrupacion,
        max(tipo_agrupacion)    tipo_agrupacion,
        count(*) filter (where interesado_tipo = 'Persona_Natural')   n_naturales,
        count(*) filter (where interesado_tipo = 'Persona_Juridica')  n_juridicas
    from cte_agrupaciones
    group by npn, agrupacion_id
)
select
    npn,
    agrupacion_id,
    nombre_agrupacion,
    n_naturales,
    n_juridicas,
    tipo_agrupacion,
    'Fail' cond_2_38
from cte_conteos
where n_juridicas > 0
  and n_naturales = 0
  and tipo_agrupacion is distinct from 'Grupo_Empresarial'
