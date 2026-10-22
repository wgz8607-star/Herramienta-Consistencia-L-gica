--regla 1.45
select ip.numero_predial_nacional, ic.numero_documento_quien_atendio , 'Fail' cond_1_45
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id ON ip.t_id = id.ilc_predio 
right join {esquema}{punto}ilc_contactovisita ic on ic.ilc_datos_adicionales =id.t_id 
where ic.numero_documento_quien_atendio !~ '^[0-9]+$'