--Regla 1.5
with tb1 as(
SELECT ip.numero_predial_nacional,
ic.ilicode condicionpredio, 
substring(ip.numero_predial_nacional,22,1)pos22, 
substring(ip.numero_predial_nacional, 23,2)pos_23_24 ,
substring(ip.numero_predial_nacional, 25,2)pos_25_26 , 
substring(ip.numero_predial_nacional, 27,4)pos_27_30
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ip.condicion_predio = ic.t_id 
where ic.ilicode = 'PH.Unidad_Predial'
)
select *, 'Fail' cond_1_5 from tb1
where pos22<>'9' or pos_23_24='00' or pos_25_26='00' or pos_27_30='0000'