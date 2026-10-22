--Regla 1.4
with tb1 as (
SELECT ip.numero_predial_nacional, 
ic.ilicode condicionpredio, 
substring(ip.numero_predial_nacional,22,1)pos22, 
substring(ip.numero_predial_nacional, 23,8)pos23_30 
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ip.condicion_predio = ic.t_id 
where ic.ilicode = 'PH.Matriz'
)
select *, 'Fail' cond_1_4 from tb1
where pos22<>'9' or pos23_30<>'00000000'