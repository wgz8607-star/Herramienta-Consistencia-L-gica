-- Regla 8.22: Para novedad de Cancelación_por_Desenglobe: el predio cancelado debe aparecer como fuente en la respectiva novedad de desenglobe.
-- Falla cuando: el predio cancelado no está como fuente en el desenglobe correspondiente.
select ip.numero_predial_nacional npn_predio
,ie.numero_predial npn_novedad
,substring(ie.numero_predial,22,1) pos_22_npn_novedad 
,ietn.ilicode tipo_novedad
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio  = ip.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode = 'Predio_Nuevo' and substring(ie.numero_predial,22,1)='5'
