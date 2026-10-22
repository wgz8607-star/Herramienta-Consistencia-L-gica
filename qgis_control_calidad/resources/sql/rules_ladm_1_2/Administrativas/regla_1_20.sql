--cond 1.20
with tb_cond_1_20 as 
(
select
lp.numero_predial
,lc.ilicode clase_suelo
,case when substring (lp.numero_predial,6,2)='00' and lc.ilicode in('Rural','Expansion_Urbana') then 'OK'
	  when substring (lp.numero_predial,6,2)<>'00' and lc.ilicode in('Urbano') then 'OK'
	  else 'Fail' end as cond_1_20
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_clasesuelotipo lc on lc.t_id =lp.clase_suelo 
)
select * from tb_cond_1_20 
where cond_1_20 ='Fail';
