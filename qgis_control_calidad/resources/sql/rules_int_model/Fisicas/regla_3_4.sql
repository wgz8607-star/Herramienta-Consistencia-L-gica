select 'terreno' capa,
count (ip.t_id) predio_relaciona,
ct.t_id ,
ct.local_id 
from {esquema}{punto}cr_terreno ct 
left join {esquema}{punto}col_uebaunit cu on cu.ue_cr_terreno = ct.t_id 
left join {esquema}{punto}ilc_predio ip on ip.t_id = cu.baunit 
group by ct.t_id
having count (ip.t_id)<>1
union
select 'u_construccion' capa,
count (ip.t_id) predio_relaciona,
cu2.t_id ,
cu2.local_id 
from {esquema}{punto}cr_unidadconstruccion cu2 
left join {esquema}{punto}col_uebaunit cu on cu.ue_cr_unidadconstruccion  = cu2.t_id 
left join {esquema}{punto}ilc_predio ip on ip.t_id = cu.baunit 
group by cu2.t_id
having count (ip.t_id)<>1
order by capa;