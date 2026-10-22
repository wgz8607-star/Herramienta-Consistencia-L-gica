--Regla 3.19
select ip.numero_predial_nacional ,
ic.ilicode condicion, 
ic2.area_construida, 
ic2.area_privada_construida,  
'Fail' cond_3_19
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ip.condicion_predio = ic.t_id 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id and cu.ue_cr_unidadconstruccion is not null
inner join {esquema}{punto}cr_unidadconstruccion cu2 on cu2.t_id = cu.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic2 on ic2.t_id = cu2.cr_caracteristicasunidadconstruccion 
where ic.ilicode not in ('PH.Unidad_Predial','Condominio.Unidad_Predial')
and (ic2.area_construida<=0 or ic2.area_privada_construida is not null)