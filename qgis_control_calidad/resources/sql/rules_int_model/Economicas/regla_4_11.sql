--regla 4.11
select ip.numero_predial_nacional,
ie.avaluo_catastral ,
ie.avaluo_catastral_terreno ,
ie.avaluo_catastral_total_unidadesconstruccion,
'Fail' cond_4_11
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_estructuraavaluo ie on ip.t_id = ie.ilc_predio_avaluo
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie3 on ie3.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie3.tipo_novedad
left join {esquema}{punto}ilc_estructuraavaluo ie2 on ie2.ilc_predio_avaluo = ip.t_id 
where (coalesce (ie.avaluo_catastral,0) <> coalesce (ie.avaluo_catastral_terreno,0) + coalesce (ie.avaluo_catastral_total_unidadesconstruccion,0) 
or coalesce (ie.avaluo_catastral,0) <= 0
or coalesce (ie.avaluo_catastral_terreno,0) + coalesce (ie.avaluo_catastral_total_unidadesconstruccion,0) <= 0)and (ietn.ilicode not like 'Cancela%' or ietn.ilicode is null)