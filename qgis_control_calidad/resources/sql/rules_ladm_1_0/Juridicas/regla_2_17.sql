with base as(
select 
lp.numero_predial
,lp.tiene_fmi 
,lp.matricula_inmobiliaria 
,case when lp.tiene_fmi =true then 'Fail' else 'Ok' end as cond_2_17
from {esquema}.lc_predio lp
where length(lp.matricula_inmobiliaria)>7
)
select * from base
where cond_2_17='Fail'