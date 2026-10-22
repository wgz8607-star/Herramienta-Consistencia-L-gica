--regla 1.23
with tb1 as (
select distinct ip.numero_predial_nacional npn_matriz,
ip2.numero_predial_nacional npn_up 
from {esquema}{punto}ilc_predio ip 
full outer join {esquema}{punto}ilc_predio ip2 on left(ip.numero_predial_nacional,22)=left(ip2.numero_predial_nacional,22) and ip.numero_predial_nacional<>ip2.numero_predial_nacional
where substring(ip.numero_predial_nacional,22,9) in ('900000000','800000000')
)
select npn_matriz, sum(case when npn_up is null then 0 else 1 end) cantidad_up,'Fail' cond_1_23 from tb1
group by npn_matriz
having sum(case when npn_up is null then 0 else 1 end)<2