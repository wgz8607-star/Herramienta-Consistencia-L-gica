--cond 1.9

with tb_cond_1_9 as
(
select 
lp.numero_predial,
case when substring (lp.numero_predial,1,2)=lp.departamento then 'OK' else 'Fail' end as cond_1_9
from {esquema}{punto}lc_predio lp 
)
select * from tb_cond_1_9
where cond_1_9='Fail';
