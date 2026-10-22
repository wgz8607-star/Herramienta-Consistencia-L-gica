--cond 1.22
with tb_cond_1_22 as
(
select 
lp.numero_predial
,lp.tiene_fmi 
,ld.tiene_area_registral 
,ld.area_registral_m2 
,case when  ld.tiene_area_registral =false and
	  		ld.area_registral_m2 =0
	  then 'OK' else 'Fail' end as cond_1_22
from {esquema}.lc_predio lp 
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
where lp.tiene_fmi =false
)
select * from tb_cond_1_22 
where cond_1_22 ='Fail';
