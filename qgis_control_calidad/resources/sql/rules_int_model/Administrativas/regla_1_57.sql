--Regla 1.57
with base_terreno as
(	select ip.numero_predial_nacional
	,substring(ip.numero_predial_nacional,18,4) terreno
	,(ascii(substring(ip.numero_predial_nacional,18,1))-64)::text||substring(ip.numero_predial_nacional,19,3) terreno_mod
	,row_number() over (partition by substring(ip.numero_predial_nacional,1,17) order by ip.numero_predial_nacional)+1000 rn
	from {esquema}{punto}ilc_predio ip 
	where substring(ip.numero_predial_nacional,18,4) ~ '^[A-Za-z9]'
)
,resultado_terreno as(
	select numero_predial_nacional, 'terreno: '||terreno info,'ilc_predio'tabla, 'Fail'  as cond_1_57 ,'Numeracion de terreno no consecutiva dentro de la manzana o vereda' descripcion from base_terreno where terreno_mod::text<>rn::text
)
,base_mz as
(	select distinct numero_predial_nacional
	,substring(numero_predial_nacional,14,4) mz_vr
	,(ascii(substring(numero_predial_nacional,14,1))-64)::text||substring(numero_predial_nacional,15,3) mz_mod
	,row_number() over (partition by substring(numero_predial_nacional,1,14) order by numero_predial_nacional)+1000 rn
	from ( select distinct substring(ip.numero_predial_nacional,1,17) numero_predial_nacional from {esquema}{punto}ilc_predio ip ) as q
	where substring(numero_predial_nacional,14,4) ~ '^[A-Za-z9]'
)
,resultado_mz as(
	select numero_predial_nacional, 'mz_vr: '||mz_vr info,'ilc_predio'tabla, 'Fail'  as cond_1_57 ,'Numeracion de manzana or vereda no consecutiva' descripcion from base_mz where mz_mod::text<>rn::text
)
select * from resultado_terreno union select * from resultado_mz