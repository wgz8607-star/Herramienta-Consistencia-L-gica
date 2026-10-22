--regla 1.52
select ip.numero_predial_nacional , 
it2.ilicode tramite,
ie.ilicode entidad,
'Fail' cond_1_52
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}lc_tramites_lc_predio ltlp on ltlp.lc_tramitesderechosterritoriales  = ip.t_id 
left join {esquema}{punto}ilc_tramitesderechosterritoriales it on it.t_id = ltlp.lc_predio 
left join {esquema}{punto}ilc_tramitetipo it2 on it2.t_id = it.tramite 
left join {esquema}{punto}ilc_entidadtipo ie on ie.t_id = it.entidad 
where (it2.ilicode <> 'Restitucion_Derechos_Territoriales' and ie.ilicode = 'URT_Unidad_Restitucion_Tierras')
or (it2.ilicode = 'Restitucion_Derechos_Territoriales' and ie.ilicode = 'ANT_Agencia_Nacional_Tierras')
