--Regla 1.7
with tb1 as(
SELECT ip.numero_predial_nacional, 
ic.ilicode condicionpredio, 
substring(ip.numero_predial_nacional, 22,5)pos_22_26 , 
substring(ip.numero_predial_nacional, 27,4)pos_27_30 
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ip.condicion_predio = ic.t_id 
where ic.ilicode = 'Condominio.Unidad_Predial'
)
select *,'Fail' cond_1_7
from tb1
where pos_22_26<>'80000' or pos_27_30='0000'