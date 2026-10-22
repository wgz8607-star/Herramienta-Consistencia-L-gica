--Regla 3.5
select ip.numero_predial_nacional, st_area(ct.geometria) area, 'Fail' cond_3_5
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id 
left join {esquema}{punto}cr_terreno ct on ct.t_id = cu.ue_cr_terreno 
where st_area(ct.geometria)::numeric<=2