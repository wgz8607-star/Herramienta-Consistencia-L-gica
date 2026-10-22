--regla 1.40
select ip.numero_predial_nacional,
etd.ilicode tipodireccion, 
ecvp.ilicode  ,
e.valor_via_principal ,
e.valor_via_generadora ,
e.numero_predio, 
e.nombre_predio, 
'Fail' cond_1_40
from {esquema}{punto}ilc_predio ip 
right join {esquema}{punto}extdireccion e on e.ilc_predio_direccion = ip.t_id 
left join {esquema}{punto}extdireccion_tipo_direccion etd on e.tipo_direccion = etd.t_id 
left join {esquema}{punto}extdireccion_clase_via_principal ecvp on ecvp.t_id = e.clase_via_principal 
where etd.ilicode = 'Estructurada' 
and (e.clase_via_principal is null or e.valor_via_principal is null or e.valor_via_generadora is null or e.numero_predio is null or e.nombre_predio is not null)

