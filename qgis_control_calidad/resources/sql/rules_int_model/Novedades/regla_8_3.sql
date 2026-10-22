-- Regla 8.3: Todo predio con novedad debe tener un soporte (ILC_DatosAdicionalesLevantamientoCatastral) asociado.
-- Falla cuando: el predio con novedad no tiene soporte documental asociado.
select ip.numero_predial_nacional, 
ietn.ilicode tiponovedad, 
substring(ip.numero_predial_nacional,22,1) pos_22_npn,
substring(ie.numero_predial,22,1) pos_22_novedad,
'Fail' cond_8_3
 from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode in ('Desenglobe_Division_Material','Desenglobe_Venta_Parcial') and 
(substring(ip.numero_predial_nacional,22,1)='2' or substring(ie.numero_predial,22,1)='2')
