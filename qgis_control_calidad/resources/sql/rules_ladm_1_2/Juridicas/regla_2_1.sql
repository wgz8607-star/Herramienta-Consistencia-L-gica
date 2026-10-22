with base as
(
select 
lp.numero_predial
,lp.tiene_fmi 
,lp.matricula_inmobiliaria 
,case when length(lp.matricula_inmobiliaria) between 1 and 7 and lp.matricula_inmobiliaria ~ '^[0-9]+$' then 'Ok' else 'Fail' end as cond_2_1
from {esquema}{punto}lc_predio lp 
where lp.tiene_fmi =true
)
select * from base
where cond_2_1 ='Fail'