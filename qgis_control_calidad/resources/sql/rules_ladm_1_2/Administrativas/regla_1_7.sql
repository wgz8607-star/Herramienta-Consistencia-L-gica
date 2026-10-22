--cond 1.7
with tb_cond_1_7 as 
(
select lp.numero_predial,
lc.ilicode condicion,
substring(lp.numero_predial,22,1),
substring(lp.numero_predial,23,8),
case when lc.ilicode='Condominio.Unidad_Predial'and 
		  substring(lp.numero_predial,22,5)='80000' and 
		  substring(lp.numero_predial,27,4) <>'0000' then 'OK'
	 else 'Fail' end as cond_1_7
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
where lc.ilicode ='Condominio.Unidad_Predial'
)
select numero_predial, condicion, cond_1_7
from tb_cond_1_7
where cond_1_7='Fail';
