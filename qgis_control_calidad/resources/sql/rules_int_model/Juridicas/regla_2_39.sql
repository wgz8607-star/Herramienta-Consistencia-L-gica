-- =============================================================================
-- Regla 2.39 — Autorreconocimiento indígena exige registro de identificación étnica
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila identificada como "3.39"
--              (errata del formato: está entre 2.38 y 2.40 en la hoja jurídica y la
--              hoja "Datos" la referencia como 2.39 — ver docs/03_hallazgos.md H-04).
-- Enunciado  : "Cuando el interesado se autorreconoce dentro de un grupo étnico
--              indígena, debe existir un registro asociado en ilc_identificacionetnica."
-- Universo   : Interesados dentro de un grupo étnico (hoja "Datos", id 42),
--              restringido a grupo_etnico = 'Etnico.Indigena'.
-- Falla si   : val_existe_registro — no hay fila en ilc_identificacionetnica para el
--                                    interesado.
--              val_nombre_pueblo   — existe el registro pero nombre_pueblo es nulo.
-- No aplica  : interesados con otro autorreconocimiento étnico o sin él.
-- Tablas     : ilc_interesado, ilc_autorreconocimientoetnicotipo,
--              ilc_identificacionetnica, ilc_nombrepueblosindigenastipo
-- Origen     : regla_2_32.sql (set anterior)
-- Salida     : documento_identidad, nombre, grupo_etnico, nombre_pueblo,
--              nombre_comunidad, val_*, cond_2_39
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 11 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Cambios frente a regla_2_32:
--   * El WHERE era `... and ii2.nombre_pueblo is null`. Con LEFT JOIN eso mezcla dos
--     situaciones distintas en una sola: (a) no existe registro de identificación
--     étnica, y (b) existe pero le falta el pueblo. El enunciado pide lo primero;
--     lo segundo también es un defecto pero se corrige de otra manera. Se separan.
--   * regla_2_32 devolvía `ii2.nombre_pueblo`, que es una FK numérica hacia
--     ilc_nombrepueblosindigenastipo, no el nombre del pueblo. El reporte mostraba
--     un t_id sin significado para quien revisa. Se resuelve el ilicode.
--   * Se añade el nombre del interesado: antes solo salía el documento.
-- =============================================================================

with cte_base as (
    select
        ii.t_id                       interesado_id,
        ii.documento_identidad,
        concat_ws(' ', ii.primer_nombre, ii.segundo_nombre,
                       ii.primer_apellido, ii.segundo_apellido,
                       ii.razon_social)  nombre,
        iae.ilicode                   grupo_etnico,
        iie.t_id                      identificacion_id,
        inp.ilicode                   nombre_pueblo,
        iie.nombre_comunidad          nombre_comunidad
    from {esquema}{punto}ilc_interesado ii
    join {esquema}{punto}ilc_autorreconocimientoetnicotipo iae
      on iae.t_id = ii.grupo_etnico
    -- el rol de la asociación se llama lc_identificacionetnica y apunta al interesado
    left join {esquema}{punto}ilc_identificacionetnica iie
           on iie.lc_identificacionetnica = ii.t_id
    left join {esquema}{punto}ilc_nombrepueblosindigenastipo inp
           on inp.t_id = iie.nombre_pueblo
    where iae.ilicode = 'Etnico.Indigena'
)
, cte_validaciones as (
    select
        b.*,
        case when b.identificacion_id is null then 'Fail' else 'Ok' end  val_existe_registro,
        case when b.identificacion_id is not null and b.nombre_pueblo is null
             then 'Fail' else 'Ok' end                                   val_nombre_pueblo
    from cte_base b
)
select distinct
    documento_identidad,
    nombre,
    grupo_etnico,
    nombre_pueblo,
    nombre_comunidad,
    val_existe_registro,
    val_nombre_pueblo,
    'Fail' cond_2_39
from cte_validaciones
where 'Fail' in (val_existe_registro, val_nombre_pueblo)
