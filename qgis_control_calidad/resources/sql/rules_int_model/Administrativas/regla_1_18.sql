--regla 1.18
with base as (
select ip.numero_predial_nacional
, ip.codigo_orip 
, ip.matricula_inmobiliaria 
, ip.area_registral_m2 
, case when ip.codigo_orip is not null 
		and ip.matricula_inmobiliaria is not null 	
		and ip.area_registral_m2=0 then 'Fail' 
	when ip.area_registral_m2 > 0
		and (ip.codigo_orip || ip.matricula_inmobiliaria is null) then 'Fail'
		else 'Ok' end cond_1_18
from {esquema}{punto}ilc_predio ip 
)
select * from base 
where cond_1_18 = 'Fail'