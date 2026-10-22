--cond 1.16
with tb_cond_1_16 as 
(
select 
lp.numero_predial 
,lp.numero_predial_anterior
,case when lp.numero_predial_anterior is null then 'Fail'
	 when length(trim(lp.numero_predial_anterior))<>20 then 'Fail'
	 else 'Ok' end as cond_1_16
from {esquema}{punto}lc_predio lp 
)
select * from tb_cond_1_16 
where cond_1_16 ='Fail';
