--regla 1.37
with tb_cond_1_37 as(
select ip.numero_predial_nacional , 
cd.numero_torres,
case when coalesce(cd.numero_torres,0) = 0 then 'Fail'
     when coalesce(cd.numero_torres,0) <>0 then 'Ok'
     else 'Fail' end as cond_1_37
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}cr_datosphcondominio cd on cd.ilc_predio = ip.t_id 
where substring(ip.numero_predial_nacional,22,9) = '800000000' 
and coalesce(cd.numero_torres,0) <> 0)
select * from tb_cond_1_37 where cond_1_37='Fail'