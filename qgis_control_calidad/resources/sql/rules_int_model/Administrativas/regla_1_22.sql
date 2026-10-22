--Regla 1.22
select ip.numero_predial_nacional, substring(ip.numero_predial_nacional,22,9)pos_22_30, cd.area_total_terreno areaPH, 'Fail' cond_1_22 
from {esquema}{punto}cr_datosphcondominio cd 
left join {esquema}{punto}ilc_predio ip ON ip.t_id = cd.ilc_predio 
where substring(ip.numero_predial_nacional,22,9) not in ('800000000','900000000')