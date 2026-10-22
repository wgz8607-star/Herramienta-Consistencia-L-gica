--regla_8_33
with tb1 as(select distinct le.numero_predial, letn.ilicode novedad
from {esquema}{punto}lc_estructuranovedadnumeropredial le 
left join {esquema}{punto}lc_estructuranovedadnumeropredial_tipo_novedad letn on letn.t_id =le.tipo_novedad 
where letn.ilicode in ('Predio_Nuevo','Cancelacion'))
select numero_predial, 'Fail' cond_8_32 from tb1
group by numero_predial 
having count(*)>1;