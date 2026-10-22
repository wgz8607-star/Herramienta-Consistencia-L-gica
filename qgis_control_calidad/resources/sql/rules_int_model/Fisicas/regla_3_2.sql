--Regla 3.2
select ip.numero_predial_nacional , ic.ilicode condicion, cu3.ilicode tipounidad, cu4.ilicode uso, 'Fail' cond_3_2
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ip.condicion_predio = ic.t_id 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id and cu.ue_cr_unidadconstruccion is not null
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu2.t_id = cu.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic2 on ic2.t_id = cu2.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}cr_unidadconstrucciontipo cu3 on cu3.t_id = ic2.tipo_unidad_construccion 
left join {esquema}{punto}cr_usouconstipo cu4 on cu4.t_id = ic2.uso 
where ic.ilicode in ('PH.Matriz', 'PH.Unidad_Predial', 'Condominio.Matriz', 'Condominio.Unidad_Predial')
and cu3.ilicode in ('Residencial','Comercial','Industrial','Institucional')
and cu4.ilicode  not like '%\_PH' AND cu4.ilicode <> 'Residencial.Depositos_Lockers'

