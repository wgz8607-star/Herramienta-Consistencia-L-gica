--cond 1.23
with tb_cond_1_23 as
(
select
lp.numero_predial,
ld.tiene_area_registral,
ld.area_registral_m2,
case when ld.area_registral_m2 is not null and ld.area_registral_m2 > 0 and ld.tiene_area_registral = true then 'OK'
       when ld.tiene_area_registral =false and ld.area_registral_m2 = 0 then 'OK'
       else 'Fail' end as cond_1_23
from {esquema}.lc_predio lp
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id
where ld.area_registral_m2 is not null)
select * from tb_cond_1_23
where cond_1_23 ='Fail';
