--cond 1.5
with tb_cond_1_5 as 
(
select lp.numero_predial,
lc.ilicode condicion,
substring(lp.numero_predial,22,1),
substring(lp.numero_predial,23,8),
case when lc.ilicode='PH.Unidad_Predial'and 
		  substring(lp.numero_predial,22,1)='9' and 
		  substring(lp.numero_predial,23,8) <>'00000000' then 'OK'
	 else 'Fail' end as cond_1_5
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
where lc.ilicode ='PH.Unidad_Predial'
)
select numero_predial, condicion, cond_1_5 
from tb_cond_1_5
where cond_1_5='Fail'; 
