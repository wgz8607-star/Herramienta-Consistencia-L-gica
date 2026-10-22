--cond 1.4
with tb_cond_1_4_1 as 
(
select lp.numero_predial,
lc.ilicode condicion,
substring(lp.numero_predial,22,1),
substring(lp.numero_predial,23,8),
case when  substring(lp.numero_predial,22,9)='900000000' then 'OK'
	 else 'Fail' end as cond_1_4
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
where lc.ilicode ='PH.Matriz'
)
,tb_cond_1_4_2 as 
(
select lp.numero_predial,
lc.ilicode condicion,
substring(lp.numero_predial,22,1),
substring(lp.numero_predial,23,8),
case when lc.ilicode='PH.Matriz'then 'OK' else 'Fail' end as cond_1_4
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
where substring(lp.numero_predial,22,9)='900000000'
)
select numero_predial, condicion, cond_1_4 
from tb_cond_1_4_1
where cond_1_4='Fail'
union 
select numero_predial, condicion, cond_1_4 
from tb_cond_1_4_2
where cond_1_4='Fail'
