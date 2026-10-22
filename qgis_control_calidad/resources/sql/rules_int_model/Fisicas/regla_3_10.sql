--Regla 3.10
select ip.numero_predial_nacional ,  cu3.ilicode tipounidad, cu4.ilicode usounidad, 'Fail' cond_3_10
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ip.condicion_predio = ic.t_id 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id 
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu2.t_id = cu.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic2 on ic2.t_id = cu2.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}cr_unidadconstrucciontipo cu3 on cu3.t_id = ic2.tipo_unidad_construccion 
left join {esquema}{punto}cr_usouconstipo cu4 on cu4.t_id = ic2.uso 
where cu3.ilicode = 'Institucional' and cu4.ilicode not like 'Institucional.%'