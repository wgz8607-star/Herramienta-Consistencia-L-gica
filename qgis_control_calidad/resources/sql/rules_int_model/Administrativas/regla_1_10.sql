--Regla 1.10
SELECT ip.numero_predial_nacional, substring(ip.numero_predial_nacional, 3,3)pos_3_5, ip.municipio  , 'Fail' cond_1_10
from {esquema}{punto}ilc_predio ip 
where substring(ip.numero_predial_nacional, 3,3)<>ip.municipio 
