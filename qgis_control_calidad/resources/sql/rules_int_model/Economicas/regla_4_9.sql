--regla 4.9
select ip.numero_predial_nacional, ietn.ilicode tiponovedad, ie2.ilc_predio_avaluo,ie2.avaluo_catastral, 'Fail' cond_4_9
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
left join {esquema}{punto}ilc_estructuraavaluo ie2 on ie2.ilc_predio_avaluo = ip.t_id 
where ietn.ilicode not like 'Cancela%' and ie2.avaluo_catastral is null