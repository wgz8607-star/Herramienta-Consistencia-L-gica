--regla 1.48
select ip.numero_predial_nacional, ic.domicilio_notificaciones , 'Fail' cond_1_48
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id ON ip.t_id = id.ilc_predio 
right join {esquema}{punto}ilc_contactovisita ic on ic.ilc_datos_adicionales =id.t_id 
where length(ic.domicilio_notificaciones)<7
