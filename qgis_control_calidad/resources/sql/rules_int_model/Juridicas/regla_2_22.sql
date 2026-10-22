-- =============================================================================
-- Regla 2.22 — El ente emisor corresponde al tipo de fuente administrativa
-- -----------------------------------------------------------------------------
-- Formato    : FO-GCT-PC01-07, hoja "2. Jurídico", fila 2.22
-- Enunciado  : "El ente emisor debe corresponder al tipo de fuente administrativa
--              diligenciado."
-- Universo   : Total de fuentes administrativas (hoja "Datos", id 40), restringido a
--              los tipos con ente emisor esperado.
-- Falla si   : val_ente — el texto de ente_emisor no coincide con ningún patrón
--              esperado para el tipo de fuente (ver tabla más abajo).
-- No aplica  : fuentes de tipo Sin_Documento, Documento_Privado y Mandato indígena
--              (no llevan ente emisor: eso lo valida 2.21); fuentes sin tipo.
-- Tablas     : ilc_predio, ilc_derecho, col_rrrfuente, ilc_fuenteadministrativa,
--              col_fuenteadministrativatipo
-- Origen     : regla_2_28.sql (set anterior)
-- Salida     : npn, fuente_tipo, ente_emisor, ente_esperado, cond_2_22
-- Verificado : 2026-07-28 · sintaxis OK y ejecutada en 4 esquemas de igac_tests
--              (a_47189_00_20260410_mod_int, iza_20260617, taller_20260513,
--              xtf_mosquera_20260330_20260407). En a_47189: 99 fila(s).
--              Falta contraste con datos de referencia para confirmar que los
--              casos detectados son los correctos.
-- -----------------------------------------------------------------------------
-- Correspondencia tipo de fuente → ente emisor esperado:
--
--   Escritura_Publica     → notaría
--   Sentencia_Judicial    → juzgado, tribunal, corte, consejo de estado
--   Acto_Administrativo   → alcaldía, gobernación, ministerio, ANT, INCODER,
--                           INCORA, agencia, instituto, superintendencia
--   Titulo_Colonial       → cualquier ente, pero diligenciado
--   Titulo_Republicano    → ídem
--   Cedula_Real           → ídem
--
-- La coincidencia es por texto libre: `ente_emisor` es TEXT(255) sin normalizar.
-- Se usa `~*` (regex sin distinción de mayúsculas) sobre el texto con tildes
-- normalizadas, en vez de la cadena de `not ilike` del set anterior.
--
-- Cambios frente a regla_2_28:
--   * 'ant' como patrón `%ant%` producía falsos negativos masivos: coincide con
--     cualquier ente que contenga esas tres letras — "SANTANDER", "GARANTÍAS",
--     "ADELANTE". Se reemplaza por un patrón con límites de palabra.
--   * Se añaden entes válidos que faltaban: corte, consejo de estado, agencia,
--     instituto, superintendencia, notaría única, etc.
--   * Se normalizan tildes con translate() para que "GOBERNACIÓN" y "GOBERNACION"
--     se traten igual. El set anterior solo capturaba la forma sin tilde.
--   * Se añade `distinct`: un predio con varios derechos sobre la misma fuente
--     generaba filas repetidas.
-- =============================================================================

with cte_base as (
    select distinct
        ip.numero_predial_nacional     npn,
        cft.ilicode                    fuente_tipo,
        ifa.ente_emisor                ente_emisor,
        -- texto normalizado: minúsculas y sin tildes, para comparar de forma estable
        lower(translate(coalesce(ifa.ente_emisor, ''),
                        'ÁÉÍÓÚÜÑáéíóúüñ',
                        'AEIOUUNaeiouun'))  ente_norm
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_derecho ide                  on ide.unidad = ip.t_id
    join {esquema}{punto}col_rrrfuente crf                on crf.rrr = ide.t_id
    join {esquema}{punto}ilc_fuenteadministrativa ifa     on ifa.t_id = crf.fuente_administrativa
    join {esquema}{punto}col_fuenteadministrativatipo cft on cft.t_id = ifa.tipo
    where cft.ilicode in ('Documento_Fuente.Escritura_Publica',
                          'Documento_Fuente.Sentencia_Judicial',
                          'Documento_Fuente.Acto_Administrativo',
                          'Documento_Fuente.Titulo_Colonial',
                          'Documento_Fuente.Titulo_Republicano',
                          'Documento_Fuente.Cedula_Real')
)
, cte_validaciones as (
    select
        b.*,
        case b.fuente_tipo
            when 'Documento_Fuente.Escritura_Publica'  then 'notaría'
            when 'Documento_Fuente.Sentencia_Judicial' then 'juzgado, tribunal, corte o consejo de estado'
            when 'Documento_Fuente.Acto_Administrativo'
                 then 'alcaldía, gobernación, ministerio, ANT, INCODER, INCORA, agencia, instituto o superintendencia'
            else 'cualquier ente, pero diligenciado'
        end  ente_esperado,
        case
            when b.fuente_tipo = 'Documento_Fuente.Escritura_Publica'
                 and b.ente_norm !~ 'notar'
                 then 'Fail'

            when b.fuente_tipo = 'Documento_Fuente.Sentencia_Judicial'
                 and b.ente_norm !~ 'juzgado|tribunal|corte|consejo de estado'
                 then 'Fail'

            when b.fuente_tipo = 'Documento_Fuente.Acto_Administrativo'
                 -- \m y \M son límites de palabra en PostgreSQL: evitan que 'ant'
                 -- coincida dentro de "SANTANDER" o "GARANTIAS"
                 and b.ente_norm !~ 'alcald|gobernacion|ministerio|\mant\M|incoder|incora|agencia|instituto|superintendencia|distrito|municipio'
                 then 'Fail'

            when b.fuente_tipo in ('Documento_Fuente.Titulo_Colonial',
                                   'Documento_Fuente.Titulo_Republicano',
                                   'Documento_Fuente.Cedula_Real')
                 and trim(b.ente_norm) = ''
                 then 'Fail'

            else 'Ok'
        end  val_ente
    from cte_base b
)
select
    npn,
    fuente_tipo,
    ente_emisor,
    ente_esperado,
    'Fail' cond_2_22
from cte_validaciones
where val_ente = 'Fail'
