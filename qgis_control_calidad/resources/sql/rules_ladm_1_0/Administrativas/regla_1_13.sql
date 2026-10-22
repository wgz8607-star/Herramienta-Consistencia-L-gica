--cond 1.13

with tb_cond_1_13 as
(
select 
lp.matricula_inmobiliaria
,count(*)
from {esquema}.lc_predio lp
where lp.matricula_inmobiliaria is not null
group by lp.matricula_inmobiliaria 
having count(*)>1
)
select * from tb_cond_1_13;
