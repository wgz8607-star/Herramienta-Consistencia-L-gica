--Regla 1.3
SELECT ip.numero_predial_nacional
, substring(ip.numero_predial_nacional,14,4)pos_14_17
, substring(ip.numero_predial_nacional,18,4)pos_18_21
, 'Fail' cond_1_3
from {esquema}{punto}ilc_predio ip 
where substring(ip.numero_predial_nacional,14,4)= '0000' 
or substring (ip.numero_predial_nacional,18,4) = '0000'