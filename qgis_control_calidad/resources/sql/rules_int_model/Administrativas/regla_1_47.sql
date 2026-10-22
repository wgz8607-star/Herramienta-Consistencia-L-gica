--regla 1.47
select ip.numero_predial_nacional, ic.autoriza_notificaciones , ic.correo_electronico , ic.celular, 'Fail' cond_1_47
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id ON ip.t_id = id.ilc_predio 
right join {esquema}{punto}ilc_contactovisita ic on ic.ilc_datos_adicionales =id.t_id 
where ic.autoriza_notificaciones = true and ic.celular is null and ic.correo_electronico is null