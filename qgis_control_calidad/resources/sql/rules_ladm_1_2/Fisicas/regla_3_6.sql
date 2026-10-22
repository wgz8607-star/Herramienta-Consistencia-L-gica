--Condicion 3_6--
select lp.numero_predial,
round(st_area(lt.geometria)::numeric,2) as areaVal,
'Fail' cond_3_6
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}col_uebaunit cu on lp.t_id = cu.baunit 
inner join {esquema}{punto}lc_terreno lt on lt.t_id = cu.ue_lc_terreno 
where round(st_area(lt.geometria)::numeric,2) < 5;