select 
ip.numero_predial_nacional,
ip2.numero_predial_nacional npn_matriz
,'Fail' cond_1_24
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_predio ip2 on substring(ip.numero_predial_nacional,1,22)||'00000000'=ip2.numero_predial_nacional 
where substring(ip.numero_predial_nacional,22,1) in ('8','9')
and substring(ip.numero_predial_nacional,23,8) <> '00000000'
and ip2.numero_predial_nacional is null
