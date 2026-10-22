--cond 1.10

with tb_cond_1_10 as
(
select 
lp.numero_predial,
case when substring (lp.numero_predial,3,3)=lp.municipio then 'OK' else 'Fail' end as cond_1_10
from {esquema}{punto}lc_predio lp 
)
select * from tb_cond_1_10
where cond_1_10='Fail';
