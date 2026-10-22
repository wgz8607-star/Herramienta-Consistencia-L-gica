--cond 1.14

with tb_cond_1_14 as 
(
select 
lp.matricula_inmobiliaria
,CASE WHEN LENGTH(TRIM(TRANSLATE(lp.matricula_inmobiliaria , ' +-.0123456789', ' '))) ='0' THEN 'OK' ELSE 'Fail' end as cond_1_14
from {esquema}{punto}lc_predio lp 
where lp.matricula_inmobiliaria is not null
)
select distinct * from tb_cond_1_14 where cond_1_14 ='Fail';
