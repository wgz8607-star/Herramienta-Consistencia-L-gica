--regla 1.49
select ip.numero_predial_nacional, ic.ilicode condicionpredio, e.complemento, 'Fail' cond_1_49
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id = ip.condicion_predio 
left join {esquema}{punto}extdireccion e on e.ilc_predio_direccion = ip.t_id 
where ic.ilicode in ('PH.Unidad_Predial','Condominio.Unidad_Predial') 
and (e.complemento !~ '(AP|BQ|BD|CS|DP|DS|ED|ET|GA|IN|LO|MZ|OF|PQ|PN|TO|UN|UR)' or e.complemento is null)
