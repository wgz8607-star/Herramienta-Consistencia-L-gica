--regla_8_31
select le.numero_predial, letn.ilicode novedad,'Fail' cond_8_31 from {esquema}{punto}lc_estructuranovedadnumeropredial le 
left join {esquema}{punto}lc_estructuranovedadnumeropredial_tipo_novedad letn on letn.t_id =le.tipo_novedad 
where letn.ilicode ='Cambio_Numero_Predial'
group by 1,2 
having count(*)>1;
