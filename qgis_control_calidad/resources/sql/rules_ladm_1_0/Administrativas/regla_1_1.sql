--cond 1.1
with tb_cond_1_1 as(
select lp.numero_predial,
lc.ilicode condicion, substring(lp.numero_predial,22,1),
substring(lp.numero_predial,23,8),
case when lc.ilicode='NPH' 				and substring(lp.numero_predial,22,1)='0' and substring(lp.numero_predial,23,8) ='00000000' then 'OK'
	 when lc.ilicode='Bien_Uso_Publico' and substring(lp.numero_predial,22,1)='3' and substring(lp.numero_predial,23,8) ='00000000' then 'OK'
	 when lc.ilicode='Via'				and substring(lp.numero_predial,22,1)='4' and substring(lp.numero_predial,23,8) ='00000000' then 'OK'
	 when lc.ilicode in ('Parque_Cementerio.Matriz','Parque_Cementerio.Unidad_Predial') 
	 									and substring(lp.numero_predial,22,1)='7' and substring(lp.numero_predial,23,8) ='00000000' then 'OK'
	 when lc.ilicode='Informal' 		and substring(lp.numero_predial,22,1)='2' and substring(lp.numero_predial,23,8) ='00000000' then 'OK'
	 else 'Fail' end as cond_1_1
	 from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
where lc.ilicode in
(
'NPH'
,'Bien_Uso_Publico'
,'Via'
,'Parque_Cementerio.Matriz'
,'Parque_Cementerio.Unidad_Predial'
,'Informal'
))
select t.numero_predial, t.condicion, t.cond_1_1  
from tb_cond_1_1 t 
where cond_1_1 ='Fail'
;