
--Regla 1.14
select ip.numero_predial_nacional, ip.codigo_orip, 'Fail' cond_1_14
from {esquema}{punto}ilc_predio ip 
where length(ip.codigo_orip)<>3 or 
ip.codigo_orip = '000'