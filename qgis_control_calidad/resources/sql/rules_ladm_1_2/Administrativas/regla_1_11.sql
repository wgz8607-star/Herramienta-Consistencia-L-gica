--cond 1.11

with tb_cond_1_11 as
(
select count(*), lp.numero_predial 
from {esquema}{punto}lc_predio lp 
group by lp.numero_predial 
having count(*)>1
)
select numero_predial, 'Fail' as cond_1_11 from tb_cond_1_11;
