-- =============================================================================
-- Regla 2.41 — Suma de participaciones en col_miembros
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.41
-- Enunciado  : "La suma de los valores de participación en la tabla col_miembros debe
--              ser igual a 1 para los interesados asociados a una misma agrupación
--              cuando el predio cuenta con FMI y se detalla el porcentaje de
--              participación. En caso contrario, la suma debe ser 0 o NULL."
-- Universo   : Total de registros en col_miembros (hoja "Datos", id 39 — ver H-05:
--              esa fila apunta por error a la regla 2.26).
-- Falla si   : val_suma_uno  — el predio tiene FMI y hay participación diligenciada,
--                              pero la suma por agrupación no es 1.
--              val_suma_cero — no se cumple el supuesto anterior y la suma no es 0
--                              ni NULL.
-- No aplica  : predios con novedad de cancelación.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrinteresado, cr_agrupacioninteresados,
--              col_miembros
-- Origen     : regla_2_26.sql (set anterior)
-- Salida     : npn, agrupacion_id, nombre_agrupacion, tiene_fmi, n_miembros,
--              n_participaciones, suma_participacion, situacion, cond_2_41
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 396 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- regla_2_26 dejaba escrita esta duda en un comentario final:
--
--     "piden que la suma sea 1 o null ¿no está ya dentro del <>1? es decir <> no
--      agarra nulls"
--
-- La duda es correcta y apunta a un defecto real: el HAVING era
--
--     having sum(cm.participacion) <> 1 and sum(...) <> 0 and sum(...) is not null
--
-- lo que solo evaluaba la rama "debe ser 1" y descartaba explícitamente los NULL.
-- Nunca se validaba la segunda mitad del enunciado ("en caso contrario la suma debe
-- ser 0 o NULL"): un predio SIN FMI con participaciones que suman 0.75 pasaba limpio.
--
-- Otros cambios frente a regla_2_26:
--   * Faltaba la condición "y se detalla el porcentaje de participación". Ahora el
--     supuesto de "suma = 1" exige que exista al menos una participación diligenciada;
--     una agrupación sin porcentajes cae en la rama de "0 o NULL", como corresponde.
--   * `ip.matricula_inmobiliaria is not null` dejaba entrar los predios con matrícula
--     igual a 0, que equivale a no tener FMI. Se usa coalesce(...) <> 0.
--   * La comparación exacta contra 1 sobre un NUMERIC de 10 decimales es frágil:
--     tres socios al 0.3333333333 suman 0.9999999999 y se reportaban como error.
--     Se compara con una tolerancia de 1e-6.
--   * El GROUP BY incluía ca.nombre, que puede ser NULL para algunas agrupaciones y
--     partir el grupo. Se saca del GROUP BY y se resuelve con max().
-- =============================================================================

with cte_miembros as (
    select
        ip.t_id                       predio_id,
        ip.numero_predial_nacional    npn,
        coalesce(ip.matricula_inmobiliaria, 0) <> 0   tiene_fmi,
        cag.t_id                      agrupacion_id,
        cag.nombre                    nombre_agrupacion,
        cm.interesado_ilc_interesado  miembro_id,
        cm.participacion              participacion
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide       on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrinteresado cri on cri.rrr = ide.t_id
    join {esquema}{punto}cr_agrupacioninteresados cag
      on cag.t_id = cri.interesado_cr_agrupacioninteresados
    join {esquema}{punto}col_miembros cm       on cm.agrupacion = cag.t_id
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
, cte_sumas as (
    select
        npn,
        agrupacion_id,
        -- fuera del GROUP BY para que un nombre nulo no parta el grupo
        max(nombre_agrupacion)                          nombre_agrupacion,
        bool_or(tiene_fmi)                              tiene_fmi,
        count(distinct miembro_id)                      n_miembros,
        count(participacion)                            n_participaciones,
        sum(participacion)                              suma_participacion
    from cte_miembros
    group by npn, agrupacion_id
)
, cte_validaciones as (
    select
        s.*,
        -- supuesto A: predio con FMI y participación efectivamente detallada
        (s.tiene_fmi and s.n_participaciones > 0)  aplica_suma_uno,
        case when s.tiene_fmi and s.n_participaciones > 0
              -- tolerancia: NUMERIC con muchos decimales no cierra exacto en 1
              and abs(coalesce(s.suma_participacion, 0) - 1) > 0.000001
             then 'Fail' else 'Ok' end             val_suma_uno,
        -- supuesto B: cualquier otro caso ⇒ la suma debe ser 0 o NULL
        case when not (s.tiene_fmi and s.n_participaciones > 0)
              and s.suma_participacion is not null
              and abs(s.suma_participacion) > 0.000001
             then 'Fail' else 'Ok' end             val_suma_cero
    from cte_sumas s
)
select
    npn,
    agrupacion_id,
    nombre_agrupacion,
    tiene_fmi,
    n_miembros,
    n_participaciones,
    suma_participacion,
    case when val_suma_uno  = 'Fail' then 'Predio con FMI: la suma debe ser 1'
         when val_suma_cero = 'Fail' then 'Sin FMI o sin porcentajes: la suma debe ser 0 o NULL'
    end  situacion,
    val_suma_uno,
    val_suma_cero,
    'Fail' cond_2_41
from cte_validaciones
where 'Fail' in (val_suma_uno, val_suma_cero)
