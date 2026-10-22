--Regla 3.1
select ip.numero_predial_nacional,
count(cu2.t_id)unidades,
'Fail' cond_3_1
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ip.condicion_predio = ic.t_id 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id 
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu2.t_id = cu.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic2 on ic2.t_id =cu2.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}cr_usouconstipo cu3 on cu3.t_id =ic2.uso 
where ic.ilicode = 'PH.Unidad_Predial'
group by ip.numero_predial_nacional
having count(cu2.t_id)<1