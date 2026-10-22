-- =============================================================================
-- Regla 2.36 — Agrupación con personas naturales y jurídicas ⇒ Grupo_Mixto
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.36
-- Enunciado  : "Cuando la agrupación de interesados de un predio esté conformada por
--              personas naturales y personas jurídicas, el tipo de agrupación debe
--              ser "Grupo_Mixto"."
-- Universo   : Agrupaciones de interesados con al menos una persona natural y al
--              menos una persona jurídica (hoja "Datos", id 36).
-- Falla si   : val_tipo — el tipo de agrupación no es 'Grupo_Mixto' (incluye el caso
--              de tipo nulo).
-- No aplica  : agrupaciones de un solo tipo (las validan 2.37 y 2.38); predios con
--              novedad de cancelación.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, cr_agrupacioninteresados,
--              col_miembros, ilc_interesado, cr_interesadotipo, col_grupointeresadotipo
-- Origen     : regla_2_23.sql (set anterior)
-- Salida     : npn, agrupacion_id, nombre_agrupacion, n_naturales, n_juridicas,
--              tipo_agrupacion, cond_2_36
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambio de fondo frente a regla_2_23:
--   El GROUP BY era `ip.numero_predial_nacional, cg.ilicode` — agrupaba por PREDIO,
--   no por AGRUPACIÓN. Un predio con dos agrupaciones distintas (una civil y una
--   empresarial) sumaba los miembros de ambas y quedaba clasificado como mixto,
--   reportando un error inexistente. El enunciado habla de "la agrupación", así que
--   la clave correcta es cr_agrupacioninteresados.t_id. Se agrupa por ella.
--
-- Otros cambios:
--   * El `else 'Fail'` del CASE anterior marcaba como error cualquier combinación no
--     contemplada, incluyendo agrupaciones de tipo Grupo_Etnico —que es un valor
--     válido del enumerado COL_GrupoInteresadoTipo—. Aquí solo se evalúa el supuesto
--     que el enunciado describe.
--   * Los LEFT JOIN se convierten en JOIN a partir de la agrupación: sin agrupación
--     no hay nada que validar, y los LEFT generaban filas con conteos en cero.
-- =============================================================================

with cte_agrupaciones as (
    -- Un registro por (predio × agrupación × miembro).
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
        -- tipo_agrupacion es constante dentro del grupo; max() evita meterla en el
        -- GROUP BY, donde un valor nulo partiría el grupo en dos
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
    'Fail' cond_2_36
from cte_conteos
-- supuesto de la regla: agrupación efectivamente mixta
where n_naturales > 0
  and n_juridicas > 0
  -- is distinct from: captura también el tipo de agrupación nulo
  and tipo_agrupacion is distinct from 'Grupo_Mixto'
