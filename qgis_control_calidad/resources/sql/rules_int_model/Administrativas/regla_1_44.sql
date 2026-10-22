--regla 1.44
select ip.numero_predial_nacional, cd.ilicode documento_atiende, 'Fail' cond_1_44
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id ON ip.t_id = id.ilc_predio 
right join {esquema}{punto}ilc_contactovisita ic on ic.ilc_datos_adicionales =id.t_id 
left join {esquema}{punto}cr_documentotipo cd ON ic.tipo_documento_quien_atendio = cd.t_id 
where cd.ilicode = 'NIT'