select  lp.numero_predial,lu2.t_ili_tid t_ili_tid_unidad_construccion,'Fail'  cond_3_23
FROM {esquema}{punto}lc_unidadconstruccion lu2 
left join {esquema}{punto}col_uebaunit cu on cu.ue_lc_unidadconstruccion = lu2.t_id
left join {esquema}{punto}lc_predio lp on lp.t_id = cu.baunit 
where lu2.total_habitaciones is null or lu2.total_banios is null or lu2.total_locales is null;
