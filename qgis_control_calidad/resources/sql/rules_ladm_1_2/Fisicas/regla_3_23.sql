select  lp.numero_predial,'Fail'  cond_3_23
FROM {esquema}{punto}lc_caracteristicasunidadconstruccion lc 
left join {esquema}{punto}lc_unidadconstruccion lu2 on lc.t_id = lu2.lc_caracteristicasunidadconstruccion 
left join {esquema}{punto}lc_construccion lc2 on lu2.lc_construccion = lc2.t_id 
left join {esquema}{punto}col_uebaunit cu on cu.ue_lc_construccion = lc2.t_id
left join {esquema}{punto}lc_predio lp on lp.t_id = cu.baunit 
where lc.total_habitaciones is null or lc.total_banios is null or lc.total_locales is null;
