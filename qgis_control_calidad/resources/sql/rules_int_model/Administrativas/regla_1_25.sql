select  ip.numero_predial_nacional,
cd.area_total_terreno, 
cd.area_total_terreno_comun, 
cd.area_total_terreno_privada,
round(st_area(ct.geometria)::numeric,2) area_geom_terreno,
'Fail' cond_1_25
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}cr_datosphcondominio cd on cd.ilc_predio = ip.t_id 
left join {esquema}{punto}col_uebaunit cu on cu.baunit= ip.t_id 
left join {esquema}{punto}cr_terreno ct on cu.ue_cr_terreno = ct.t_id 
where substring(ip.numero_predial_nacional,22,9)='900000000' 
and (cd.area_total_terreno_privada <>0 
	or cd.area_total_terreno <> round(st_area(ct.geometria)::numeric,2)
	or cd.area_total_terreno_comun <> round(st_area(ct.geometria)::numeric,2)
	)