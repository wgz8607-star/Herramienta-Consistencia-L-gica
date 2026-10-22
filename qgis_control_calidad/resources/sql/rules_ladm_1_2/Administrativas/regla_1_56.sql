--cond 1.56 (nueva)
SELECT  lp.numero_predial,lc.domicilio_notificaciones ,'Fail' cond_1_56 FROM {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
inner join {esquema}{punto}lc_contactovisita lc on lc.lc_datos_adicionales =ld.t_id 
where length(coalesce(lc.domicilio_notificaciones,''))<7
