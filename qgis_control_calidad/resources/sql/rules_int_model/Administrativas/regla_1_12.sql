--Regla 1.12
select lp.matricula_inmobiliaria matricula, 
count(lp.numero_predial_nacional) conteo
,'Fail' cond_1_12
from {esquema}{punto}ilc_predio lp 
where matricula_inmobiliaria is not null
group by  lp.matricula_inmobiliaria
having count(lp.numero_predial_nacional)>1
