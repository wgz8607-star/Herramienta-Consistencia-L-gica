--Regla 3.12
select ip.numero_predial_nacional ,  cu2.planta_ubicacion , 'Fail' cond_3_12
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ip.condicion_predio = ic.t_id 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id 
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu2.t_id = cu.ue_cr_unidadconstruccion 
where cu2.planta_ubicacion <=0