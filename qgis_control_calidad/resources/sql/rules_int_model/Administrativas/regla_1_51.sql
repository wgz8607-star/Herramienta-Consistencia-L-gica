--regla 1.51
with tb_cond_1_51 as(
select 
ip.numero_predial_nacional npn_formal,
substring(ip.numero_predial_nacional,22,1) cond_npn_formal ,
ip2.numero_predial_nacional npn_informal,
substring(ip2.numero_predial_nacional,22,1) cond_npn_informal,
case when substring(ip.numero_predial_nacional,22,1) ='2' or substring(ip2.numero_predial_nacional,22,1)<>'2' then 'Fail' else 'Ok' end as cond_1_51
from {esquema}{punto}ilc_predio_informalidad ipi
left join {esquema}{punto}ilc_predio ip  on ipi.igc_predio_formal  = ip.t_id 
left join {esquema}{punto}ilc_predio ip2 on ip2.t_id= ipi.igc_predio_informal
)
select * from tb_cond_1_51 where cond_1_51='Fail'