--regla 1.43
select ip.numero_predial_nacional,  etd.ilicode tipodireccion, e.letra_via_principal, e.letra_via_generadora, 'Fail' cond_1_43
from {esquema}{punto}ilc_predio ip 
right join {esquema}{punto}extdireccion e on e.ilc_predio_direccion = ip.t_id 
left join {esquema}{punto}extdireccion_tipo_direccion etd on e.tipo_direccion = etd.t_id 
where etd.ilicode = 'Estructurada'
and ((e.letra_via_principal is not null and e.letra_via_principal !~ '(^[a-zA-Z]+$)')
or (e.letra_via_generadora  is not null and e.letra_via_generadora !~'(^[a-zA-Z]+$)'))