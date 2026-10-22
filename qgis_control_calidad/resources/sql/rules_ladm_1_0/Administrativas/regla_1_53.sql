WITH base AS (
    SELECT 
        lp.numero_predial,
        lc.correo_electronico,
        lc.celular,
        lc.autoriza_notificaciones,
        CASE 
            WHEN lc.autoriza_notificaciones IS false and lc.correo_electronico is NULL then 'Ok'
            WHEN lc.autoriza_notificaciones IS TRUE AND (lc.correo_electronico ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]+$') or (lc.celular is not null 
	    and lc.celular  ~ '^[0-9]+$' 
	    and length(lc.celular)=10) THEN 'Ok'
            ELSE 'Fail' 
        END AS cond_1_53
    FROM 
        {esquema}.lc_predio lp 
        INNER JOIN {esquema}.lc_datosadicionaleslevantamientocatastral ld ON ld.lc_predio = lp.t_id 
        INNER JOIN {esquema}.lc_contactovisita lc ON lc.lc_datos_adicionales = ld.t_id 
)
SELECT * FROM base WHERE cond_1_53 = 'Fail'

