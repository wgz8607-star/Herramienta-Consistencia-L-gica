-- =============================================================================
-- Regla 2.25 — Mismo documento en interesados distintos
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.25
-- Enunciado  : "No deben existir registros de interesados distintos con el mismo
--              número de documento de identificación. (Mismo documento, diferente
--              interesado)"
-- Universo   : Total de interesados (hoja "Datos", id 41).
-- Falla si   : un mismo documento_identidad aparece en dos o más registros de
--              ilc_interesado. Se reportan por separado dos situaciones:
--                'Nombres distintos'  → personas diferentes con el mismo documento
--                                       (error grave de identificación)
--                'Registro duplicado' → mismo nombre y mismo documento repetidos
-- No aplica  : documentos de tipo Secuencial (son consecutivos asignados por el
--              sistema y su unicidad la valida 2.30); documentos vacíos o nulos.
-- Tablas     : ilc_interesado, cr_interesadotipo, cr_documentotipo
-- Origen     : regla_2_31.sql (set anterior)
-- Salida     : documento_identidad, documento_tipo, n_registros, n_nombres,
--              situacion, nombres, cond_2_25
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 0 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambios frente a regla_2_31:
--   * regla_2_31 devolvía solo el documento y el conteo. Quien revisaba tenía que
--     volver a la base para saber de quién se trataba. Ahora se listan los nombres.
--   * Se distingue "mismo documento, personas distintas" de "registro duplicado":
--     el primero es un error de captura de identidad, el segundo un problema de
--     deduplicación. Se corrigen de forma distinta.
--   * Se excluyen documentos nulos o vacíos: agrupaban todos los registros
--     incompletos en un solo falso positivo gigante. Su ausencia la reporta 2.30.
--   * Se excluye el tipo Secuencial, cuya repetición tiene otro significado.
-- =============================================================================

with cte_base as (
    select
        ii.t_id                    interesado_id,
        trim(ii.documento_identidad)  documento_identidad,
        cit.ilicode                interesado_tipo,
        cdt.ilicode                documento_tipo,
        trim(regexp_replace(
            upper(translate(
                concat_ws(' ',
                          nullif(trim(ii.primer_nombre),   ''),
                          nullif(trim(ii.segundo_nombre),  ''),
                          nullif(trim(ii.primer_apellido), ''),
                          nullif(trim(ii.segundo_apellido),''),
                          nullif(trim(ii.razon_social),    '')),
                'áéíóúüñÁÉÍÓÚÜÑ',
                'aeiouunAEIOUUN')),
            '\s+', ' ', 'g'))      nombre_normalizado
    from {esquema}{punto}ilc_interesado ii
    left join {esquema}{punto}cr_interesadotipo cit on cit.t_id = ii.tipo
    left join {esquema}{punto}cr_documentotipo cdt  on cdt.t_id = ii.tipo_documento
    where coalesce(trim(ii.documento_identidad), '') <> ''
      and coalesce(cdt.ilicode, '') <> 'Secuencial'
)
, cte_grupos as (
    select
        documento_identidad,
        max(documento_tipo)                    documento_tipo,
        count(*)                               n_registros,
        count(distinct nombre_normalizado)     n_nombres,
        string_agg(distinct nombre_normalizado, ' || ' order by nombre_normalizado) nombres
    from cte_base
    group by documento_identidad
    having count(*) > 1
)
select
    documento_identidad,
    documento_tipo,
    n_registros,
    n_nombres,
    case when n_nombres > 1 then 'Nombres distintos'
         else 'Registro duplicado' end  situacion,
    -- El listado se acota a 300 caracteres: un documento compartido por cientos de
    -- registros (típico del '0' de relleno) generaba una celda ilegible de miles de
    -- caracteres que rompe el reporte. n_nombres da la magnitud real.
    case when length(nombres) > 300
         then left(nombres, 300) || ' … (+' || (n_nombres - 1) || ' más)'
         else nombres end             nombres,
    'Fail' cond_2_25
from cte_grupos
order by n_registros desc, documento_identidad
