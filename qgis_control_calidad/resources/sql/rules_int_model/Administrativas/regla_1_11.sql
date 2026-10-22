--Regla 1.11
select ip.numero_predial_nacional, count(ip.numero_predial_nacional) conteo, 'Fail' cond_1_11
from {esquema}{punto}ilc_predio ip 
group by ip.numero_predial_nacional 
having count(ip.numero_predial_nacional)>1