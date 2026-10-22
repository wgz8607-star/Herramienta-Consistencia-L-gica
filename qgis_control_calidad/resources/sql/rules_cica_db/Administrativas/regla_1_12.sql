--regla 1.12
with base as (
select cp.numero_predial
, cp.tiene_fmi 
, cp.circulo_registral 
, cp.matricula 
, cp.coordinador
, cp.usuario as reconocedor
, case 	WHEN NULLIF(cp.tiene_fmi ,'') IS NULL THEN 'Fail'
		when cp.tiene_fmi = 'SI' and nullif(cp.circulo_registral,'') is null then 'Fail'
		when cp.tiene_fmi = 'SI' and nullif(cp.matricula,'') is null then 'Fail' 
		when cp.tiene_fmi = 'NO' and nullif(cp.circulo_registral,'') is not null then 'Fail'
		when cp.tiene_fmi = 'NO' and nullif(cp.matricula,'') is not null then 'Fail' 
		else 'OK' end cond_1_12
from {esquema}{punto}cica_predio cp 
where cp.estado = 'ACTIVO'	
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
select distinct * from base 
where cond_1_12 = 'Fail'