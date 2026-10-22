select
lu.t_id
,lu.t_ili_tid 
,lu.area_construida 
,round(st_area(lu.geometria)::numeric,1) area_geometrica
,abs((lu.area_construida-round(st_area(lu.geometria)::numeric,1))/lu.area_construida)*100 porcentaje_error
,'Fail' cond_3_38	
	from {esquema}.lc_unidadconstruccion lu 
	where 1=1
and abs((lu.area_construida-round(st_area(lu.geometria)::numeric,1))/lu.area_construida)*100>1
