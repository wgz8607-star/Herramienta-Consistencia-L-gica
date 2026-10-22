--regla_8_34
select distinct ar.numero_predial, letn.ilicode novedad, 'Fail' cond_8_43 from {esquema_r1}.{tabla_r1} ar 
left join {esquema}{punto}lc_estructuranovedadnumeropredial le on le.numero_predial =ar.numero_predial 
left join {esquema}{punto}lc_estructuranovedadnumeropredial_tipo_novedad letn on letn.t_id =le.tipo_novedad and letn.ilicode = 'Cambio_Numero_Predial'
where substring(ar.numero_predial,22,1)='5'
and coalesce(letn.ilicode,'')<>'Cambio_Numero_Predial'