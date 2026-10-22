--regla 1.46
select ip.numero_predial_nacional, ic.correo_electronico , 'Fail' cond_1_46
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id ON ip.t_id = id.ilc_predio 
right join {esquema}{punto}ilc_contactovisita ic on ic.ilc_datos_adicionales =id.t_id 
where ic.correo_electronico is not null and ic.correo_electronico  
!~ ('^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}])|(([a-zA-Z\u0400-\uffff\-0-9]+\.)+[a-zA-Z\u0400-\uffff]{{2,}}))$')
