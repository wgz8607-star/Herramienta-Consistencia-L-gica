select 'terreno' capa ,ct.t_ili_tid t_ili_tid, count(ip.t_id),'Fail' as cond_3_5
from {esquema}{punto}lc_terreno ct 
left join {esquema}{punto}col_uebaunit cu on cu.ue_lc_terreno = ct.t_id 
left join {esquema}{punto}lc_predio ip on ip.t_id = cu.baunit 
group by ct.t_ili_tid
having count(ip.t_id)>1
union all 
select 'unidad_construccion' capa ,ct.t_ili_tid t_ili_tid, count(ip.t_id),'Fail' as cond_3_5
from {esquema}{punto}lc_unidadconstruccion ct 
left join {esquema}{punto}col_uebaunit cu on cu.ue_lc_unidadconstruccion = ct.t_id 
left join {esquema}{punto}lc_predio ip on ip.t_id = cu.baunit 
group by ct.t_ili_tid
having count(ip.t_id)>1
union all 
select 'construccion' capa ,ct.t_ili_tid t_ili_tid, count(ip.t_id),'Fail' as cond_3_5
from {esquema}{punto}lc_construccion ct 
left join {esquema}{punto}col_uebaunit cu on cu.ue_lc_construccion = ct.t_id 
left join {esquema}{punto}lc_predio ip on ip.t_id = cu.baunit 
group by ct.t_ili_tid
having count(ip.t_id)>1