--regla 1.14
with base as (
select numero_predial 
, matricula 
, length(matricula) largo_FMI
, cp.coordinador
, cp.usuario
, case 	when matricula !~ '^[0-9]+$' then 'Fail' 
		when coalesce(matricula,'0')::numeric not between 1 and 9999999 then 'Fail'
		else 'Ok' end cond_1_14
from {esquema}{punto}cica_predio cp 
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
select distinct 
b.numero_predial
, b.matricula
, b.largo_fmi
, b.coordinador
, b.usuario as reconocedor
, b.cond_1_14
from base b
where nullif(b.matricula,'') is not null
and b.cond_1_14 = 'Fail'