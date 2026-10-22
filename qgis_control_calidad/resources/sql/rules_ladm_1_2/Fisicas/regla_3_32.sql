select lu.t_ili_tid t_ili_tid_unidad_c, lc.t_ili_tid t_ili_tid_construccion, lc4.ilicode tipo_construccion_uc, lc3.ilicode tipo_construccion_construccion,
'Fail' cond_3_32
from {esquema}{punto}lc_unidadconstruccion lu 
inner join {esquema}{punto}lc_caracteristicasunidadconstruccion lc2 on lc2.t_id =lu.lc_caracteristicasunidadconstruccion 
inner join {esquema}{punto}lc_construccion lc on lc.t_id =lu.lc_construccion 
left join {esquema}{punto}lc_construcciontipo lc4 on lc4.t_id=lc2.tipo_construccion 
left join {esquema}{punto}lc_construcciontipo lc3 on lc3.t_id=lc.tipo_construccion
where lc4.ilicode<>lc3.ilicode 