
--Regla 1.9

SELECT ip.numero_predial_nacional, substring(ip.numero_predial_nacional, 1,2)pos_1_2, ip.departamento , 'Fail' cond_1_9
from {esquema}{punto}ilc_predio ip 
where substring(ip.numero_predial_nacional, 1,2)<>ip.departamento 