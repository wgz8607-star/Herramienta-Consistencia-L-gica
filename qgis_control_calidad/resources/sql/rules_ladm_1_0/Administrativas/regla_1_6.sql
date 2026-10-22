--cond 1.6
with tb_cond_1_6_1 as 
(
select lp.numero_predial,
lc.ilicode condicion,
substring(lp.numero_predial,22,1),
substring(lp.numero_predial,23,8),
case when  substring(lp.numero_predial,22,9)='800000000' then 'OK'
	 else 'Fail' end as cond_1_6
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
where lc.ilicode ='Condominio.Matriz'
)
,tb_cond_1_6_2 as 
(
select lp.numero_predial,
lc.ilicode condicion,
substring(lp.numero_predial,22,1),
substring(lp.numero_predial,23,8),
case when lc.ilicode='Condominio.Matriz'then 'OK' else 'Fail' end as cond_1_6
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
where substring(lp.numero_predial,22,9)='800000000'
)
select numero_predial, condicion, cond_1_6 
from tb_cond_1_6_1
where cond_1_6='Fail'
union 
select numero_predial, condicion, cond_1_6 
from tb_cond_1_6_2
where cond_1_6='Fail'
