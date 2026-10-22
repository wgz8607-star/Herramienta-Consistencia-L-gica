--regla 1.60
select ip.numero_predial, ic.ilicode condicionpredio, e.complemento, 'Fail' cond_1_60
from {esquema}{punto}lc_predio ip 
left join {esquema}{punto}lc_condicionprediotipo ic on ic.t_id = ip.condicion_predio 
left join {esquema}{punto}extdireccion e on e.lc_predio_direccion = ip.t_id 
where ic.ilicode in ('PH.Unidad_Predia','Condominio.Unidad_Predial') and e.complemento !~ '(AP|BQ|BD|CS|ED|ET|GA|IN|LO|MZ|OF|PQ|PN|TO|UN|UR)'