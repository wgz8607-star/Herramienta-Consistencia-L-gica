-- =============================================================================
-- Regla 2.21 — Congruencia de ente emisor / número / fecha con el tipo de fuente
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.21
-- Enunciado  : "Los valores de ente emisor, número de fuente administrativa y fecha
--              de documento fuente deben ser congruentes con el tipo de fuente
--              administrativa asignado."
-- Universo   : Total de fuentes administrativas (hoja "Datos", id 40).
-- Falla si   : el patrón de campos diligenciados no corresponde al tipo de fuente,
--              según la matriz documentada más abajo. val_congruencia = 'Fail'.
-- No aplica  : fuentes administrativas sin tipo asignado (lo reporta 2.20).
-- Tablas     : ilc_predio, ilc_derecho, col_rrrfuente, ilc_fuenteadministrativa,
--              col_fuenteadministrativatipo
-- Origen     : regla_2_27.sql (set anterior)
-- Salida     : npn, fuente_tipo, ente_emisor, numero_fuente,
--              fecha_documento_fuente, observacion, motivo, cond_2_21
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 1 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Matriz de congruencia (— = no debe estar diligenciado, X = debe estarlo):
--
--   Tipo de fuente                              ente  número  fecha  observación
--   Documento_Fuente.Acto_Administrativo          X      X       X       -
--   Documento_Fuente.Sentencia_Judicial           X      X       X       -
--   Documento_Fuente.Escritura_Publica            X      X       X       -
--   Documento_Fuente.Titulo_Colonial              X      —       X       -
--   Documento_Fuente.Titulo_Republicano           X      —       X       -
--   Documento_Fuente.Cedula_Real                  X      —       X       -
--   Documento_Fuente.Documento_Privado            —      —       X       X
--   Fuente_Informativa_Intercultural.Mandato_...  —      —       X       X
--   Sin_Documento                                 —      —       —       -
--
-- OJO con 'Documento_Privado' (hallazgo H-02): la tabla col_fuenteadministrativatipo
-- contiene las DOS formas —'Documento_Fuente.Documento_Privado' del enumerado
-- extendido y 'Documento_Privado' suelto, heredado del enumerado base LADM— y los
-- esquemas usan una u otra según quién cargó los datos. Se aceptan ambas.
--
-- Otros cambios frente a regla_2_27:
--   * Se añade una columna `motivo` que dice qué falló, en vez de dejar al revisor
--     reconstruirlo desde un OR de cinco ramas.
--   * Los campos de texto se comparan contra vacío además de NULL: un ente_emisor
--     con cadena vacía pasaba la validación anterior.
--   * Los tipos no contemplados en la matriz (Otro_Documento_fuente, Auto,
--     Protocolizacion_Notarial, Otros_Documentos) NO se evalúan. El formato no
--     define su patrón esperado; inventarlo produciría falsos positivos.
--     → pendiente de definición funcional (ver docs/03_hallazgos.md).
-- =============================================================================

with cte_base as (
    select distinct
        ip.numero_predial_nacional     npn,
        ifa.t_id                       fuente_id,
        cft.ilicode                    fuente_tipo,
        ifa.ente_emisor                ente_emisor,
        ifa.numero_fuente              numero_fuente,
        ifa.fecha_documento_fuente     fecha_documento_fuente,
        ifa.observacion                observacion
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide                     on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrfuente crf                   on crf.rrr = ide.t_id
    join {esquema}{punto}ilc_fuenteadministrativa ifa        on ifa.t_id = crf.fuente_administrativa
    join {esquema}{punto}col_fuenteadministrativatipo cft    on cft.t_id = ifa.tipo
)
, cte_flags as (
    -- Normalización: un campo "diligenciado" es no nulo y no vacío tras trim.
    select
        b.*,
        coalesce(trim(b.ente_emisor), '')            <> ''      tiene_ente,
        coalesce(trim(b.numero_fuente::text), '')    <> ''      tiene_numero,
        b.fecha_documento_fuente is not null                    tiene_fecha,
        coalesce(trim(b.observacion), '')            <> ''      tiene_observacion
    from cte_base b
)
, cte_validaciones as (
    select
        f.*,
        case
            -- Documentos con entidad emisora, número y fecha
            when f.fuente_tipo in ('Documento_Fuente.Acto_Administrativo',
                                   'Documento_Fuente.Sentencia_Judicial',
                                   'Documento_Fuente.Escritura_Publica')
                 and not (f.tiene_ente and f.tiene_numero and f.tiene_fecha)
                 then 'Falta ente emisor, número o fecha'

            -- Títulos históricos: sin número de fuente
            when f.fuente_tipo in ('Documento_Fuente.Titulo_Colonial',
                                   'Documento_Fuente.Titulo_Republicano',
                                   'Documento_Fuente.Cedula_Real')
                 and not (f.tiene_ente and not f.tiene_numero and f.tiene_fecha)
                 then 'Título histórico: requiere ente y fecha, sin número de fuente'

            -- Documento privado y mandato indígena: sin ente ni número, con fecha y observación
            when f.fuente_tipo in ('Documento_Fuente.Documento_Privado',
                                   'Documento_Privado',
                                   'Fuente_Informativa_Intercultural.Mandato_Propio_Indigena')
                 and not (not f.tiene_ente and not f.tiene_numero
                          and f.tiene_fecha and f.tiene_observacion)
                 then 'Requiere fecha y observación, sin ente emisor ni número de fuente'

            -- Sin documento: no debe haber nada diligenciado
            when f.fuente_tipo = 'Sin_Documento'
                 and (f.tiene_ente or f.tiene_numero or f.tiene_fecha)
                 then 'Sin_Documento no debe tener ente, número ni fecha'

            else null
        end  motivo
    from cte_flags f
)
select
    npn,
    fuente_tipo,
    ente_emisor,
    numero_fuente,
    fecha_documento_fuente,
    observacion,
    motivo,
    'Fail' cond_2_21
from cte_validaciones
where motivo is not null
