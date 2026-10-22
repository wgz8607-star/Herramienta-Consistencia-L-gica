--regla 1.50
with tb_cond_1_50 as(
select 
ip.numero_predial_nacional informal, 
substring(ip.numero_predial_nacional,22,1) cons_22_informal, 
ip2.numero_predial_nacional formal, 
substring(ip2.numero_predial_nacional,22,1) cons_22_formal, 
case when ip2.numero_predial_nacional is null then 'Fail'
	 when substring(ip2.numero_predial_nacional,22,1)='2' then 'Fail'
	 when substring(ip2.numero_predial_nacional,22,1)<>'2' then 'OK'
	 else 'Fail' end as cond_1_50
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_predio_informalidad ipi on ipi.igc_predio_informal  = ip.t_id 
left join {esquema}{punto}ilc_predio ip2 on ip2.t_id = ipi.igc_predio_formal 
where substring(ip.numero_predial_nacional,22,1) = '2')
select distinct * from tb_cond_1_50
where cond_1_50 ='Fail'