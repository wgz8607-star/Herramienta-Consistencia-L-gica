--Regla 1.13
select ip.numero_predial_nacional, ip.matricula_inmobiliaria , 'Fail' cond_1_13
from {esquema}{punto}ilc_predio ip 
where ip.matricula_inmobiliaria < 1 or ip.matricula_inmobiliaria > 99999999