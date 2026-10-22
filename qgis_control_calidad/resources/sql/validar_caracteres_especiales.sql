CREATE OR REPLACE FUNCTION public.validar_caracteres_especiales(esquema text)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
DECLARE
    rec RECORD;
    tbl_name text;
    col_name text;
    query text;
begin
	execute 'CREATE TABLE IF NOT EXISTS public.resultado_caracteres_especiales(table_name text, column_name text, invalid_value text);';
       -- Limpiar la tabla de resultados antes de insertar nuevos datos
    TRUNCATE public.resultado_caracteres_especiales;
    FOR rec IN 
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE data_type IN ('character varying', 'text')
        and table_schema=$1
        and table_name not like '%tipo%'
        and table_name not like '%snr_%'
        and table_name not like '%gc_%'
        and table_name not like 't_ili2db%'
    LOOP
        tbl_name := quote_ident(rec.table_schema) || '.' || quote_ident(rec.table_name);
        col_name := quote_ident(rec.column_name);
        -- Crear la consulta con los caracteres especiales especificados
        query := 'INSERT INTO public.resultado_caracteres_especiales (table_name, column_name, invalid_value) ' ||
                 'SELECT ' || quote_literal(tbl_name) || ', ' || quote_literal(col_name) || ', ' || col_name || ' ' ||
                 'FROM ' || tbl_name || ' ' ||
                 'WHERE ' || col_name || ' ~ ''[\*\~\{\}\[\]\¨\n\t]'';';        
        EXECUTE query;
    END LOOP;
END;
$function$
;
