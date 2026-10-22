-- =============================================================================
-- Regla 2.24 — Mismo nombre / razón social con distinto documento (homónimos)
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.24
-- Enunciado  : "Los registros de interesados cuyos nombres y apellidos, o cuya razón
--              social, sean idénticos deberán tener un número de documento de
--              identificación diferente. (Mismo interesado, diferente documento)"
-- Universo   : Total de interesados (hoja "Datos", id 41).
-- Falla si   : dos o más registros de ilc_interesado comparten exactamente el mismo
--              nombre completo (o razón social) y tienen números de documento
--              DIFERENTES entre sí.
-- No aplica  : interesados sin nombre ni razón social diligenciados (lo reporta 2.32).
-- Tablas     : ilc_interesado, cr_interesadotipo, cr_documentotipo
-- Origen     : regla_2_30.sql (set anterior)
-- Salida     : nombre_normalizado, n_documentos, documento_identidad,
--              interesado_tipo, documento_tipo, cond_2_24
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 30 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Naturaleza de la regla: es una LISTA DE VERIFICACIÓN, no un error duro. Dos
-- personas distintas pueden llamarse igual (homónimos legítimos) y por eso el
-- formato anterior la anotaba como "Excepción Homónimos". El revisor decide caso
-- a caso si marca excepción o corrige.
--
-- Cambios frente a regla_2_30:
--   * concat() sin separadores hacía colisionar nombres distintos: "JUAN CARLOS" +
--     "PEREZ" y "JUAN" + "CARLOS PEREZ" producían la misma cadena. Ahora se usa
--     concat_ws(' ', ...), que además ignora los NULL.
--   * Se normaliza a mayúsculas, sin tildes y con espacios colapsados, para que
--     "José Pérez" y "JOSE  PEREZ" se detecten como el mismo nombre. Antes cualquier
--     diferencia de formato ocultaba el caso.
--   * Se excluyen los registros sin nombre ni razón social: antes todos ellos
--     compartían la cadena vacía y se reportaban entre sí como homónimos.
--   * Se añaden tipo de interesado y tipo de documento al resultado, que son los
--     datos que el revisor necesita para decidir.
-- =============================================================================

with cte_base as (
    select
        ii.t_id                                   interesado_id,
        ii.documento_identidad                    documento_identidad,
        cit.ilicode                               interesado_tipo,
        cdt.ilicode                               documento_tipo,
        -- Nombre canónico: mayúsculas, sin tildes, espacios colapsados.
        -- Para persona jurídica el nombre relevante es la razón social.
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
            '\s+', ' ', 'g'))                     nombre_normalizado
    from {esquema}{punto}ilc_interesado ii
    left join {esquema}{punto}cr_interesadotipo cit on cit.t_id = ii.tipo
    left join {esquema}{punto}cr_documentotipo cdt  on cdt.t_id = ii.tipo_documento
)
, cte_con_nombre as (
    -- Sin nombre no hay homonimia posible: esos registros los reporta la regla 2.32.
    select * from cte_base where nombre_normalizado <> ''
)
, cte_grupos as (
    -- Nombres que aparecen con MÁS DE UN documento distinto.
    -- count(distinct ...) sobre el documento: si el mismo interesado está duplicado
    -- con idéntico documento, eso es un problema de otra naturaleza y no cae aquí.
    select
        nombre_normalizado,
        count(distinct documento_identidad) n_documentos
    from cte_con_nombre
    group by nombre_normalizado
    having count(distinct documento_identidad) > 1
)
select
    g.nombre_normalizado,
    g.n_documentos,
    c.documento_identidad,
    c.interesado_tipo,
    c.documento_tipo,
    'Fail' cond_2_24
from cte_grupos g
join cte_con_nombre c on c.nombre_normalizado = g.nombre_normalizado
order by g.nombre_normalizado, c.documento_identidad
