--cond 1.15

with tb_cond_1_15 as 
(
select
lp.codigo_orip,
case when length(lp.codigo_orip)<>3 then 'Fail' else 'OK' end as cond_1_15
from {esquema}.lc_predio lp
where lp.codigo_orip is not null
)
select * from tb_cond_1_15 
where cond_1_15 ='Fail';
