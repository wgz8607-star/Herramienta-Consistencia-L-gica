--regla 1.42 
select ip.numero_predial_nacional, substring(ip.numero_predial_nacional,6,2)pos_6_7 ,  etd.ilicode tipodireccion, 'Fail' cond_1_42
from {esquema}{punto}ilc_predio ip 
right join {esquema}{punto}extdireccion e on e.ilc_predio_direccion = ip.t_id 
left join {esquema}{punto}extdireccion_tipo_direccion etd on e.tipo_direccion = etd.t_id 
where (substring(ip.numero_predial_nacional,6,2) <> '00' and etd.ilicode<>'Estructurada')
or (substring(ip.numero_predial_nacional,6,2) = '00' and etd.ilicode<>'No_Estructurada')