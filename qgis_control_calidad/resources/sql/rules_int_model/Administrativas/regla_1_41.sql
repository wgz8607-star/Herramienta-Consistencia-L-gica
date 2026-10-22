--regla 1.41
select ip.numero_predial_nacional, etd.ilicode tipodireccion, e.clase_via_principal , e.valor_via_principal , e.valor_via_generadora , e.numero_predio, e.nombre_predio, 'Fail' cond_1_41
from {esquema}{punto}ilc_predio ip 
right join {esquema}{punto}extdireccion e on e.ilc_predio_direccion = ip.t_id 
left join {esquema}{punto}extdireccion_tipo_direccion etd on e.tipo_direccion = etd.t_id 
where etd.ilicode = 'No_Estructurada' 
and (e.clase_via_principal is not null or e.valor_via_principal is not null or e.valor_via_generadora is not null or e.numero_predio is not null or e.nombre_predio is null)