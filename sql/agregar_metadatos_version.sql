-- Ejecutar en la base de datos sentencias, con permisos ALTER sobre las tablas.
-- No modifica las descripciones de reglas ni su bandera activa.
BEGIN;

DO $$
DECLARE
    nombre_tabla TEXT;
BEGIN
    FOREACH nombre_tabla IN ARRAY ARRAY[
        'reglas_interno_v3_07_09_2026',
        'reglas_interno_v2_29_07_2024',
        'reglas_cica_v3_07_09_2026',
        'reglas_cica_v2_29_07_2024',
        'reglas_cargue_snc_cica',
        'reglas_cargue_snc_xtf'
    ] LOOP
        IF to_regclass(format('public.%I', nombre_tabla)) IS NULL THEN
            RAISE NOTICE 'Se omite public.%: la tabla no existe', nombre_tabla;
            CONTINUE;
        END IF;
        EXECUTE format(
            'ALTER TABLE public.%I '
            'ADD COLUMN IF NOT EXISTS descripcion_version TEXT NOT NULL DEFAULT '''', '
            'ADD COLUMN IF NOT EXISTS version_publicada BOOLEAN NOT NULL DEFAULT TRUE',
            nombre_tabla
        );
    END LOOP;
END $$;

COMMIT;

-- Se conserva publicada una versión existente si tiene reglas activas.
-- Para cada versión, SOLO se leen los metadatos de su primera fila según:
-- ORDER BY orden NULLS LAST, componente, codigo_regla
-- La primera fila puede tener activa = FALSE: sigue siendo la cabecera.
-- Mantener estable ese orden; si se sustituye la primera regla, transferir
-- los metadatos a la nueva primera fila.
