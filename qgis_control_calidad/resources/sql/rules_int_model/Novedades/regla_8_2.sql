-- Regla 8.2: El predio cancelado por desenglobe debe existir en el R1.
-- Falla cuando: un predio con novedad Cancelacion_por_Desenglobe no se encuentra en el archivo R1.
-- Nota: los predios nuevos resultantes del desenglobe (DVP/DDM) no deben verificarse contra R1 ya que son predios nuevos.
select
ip.numero_predial_nacional,
ietn.ilicode tiponovedad,
ie.numero_predial np_novedad,
rdcr.numero_predial npn_r1,
'Fail' cond_8_2
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
left join {esquema_r1}{punto}{tabla_r1} rdcr on rdcr.numero_predial = ip.numero_predial_nacional
where ietn.ilicode = 'Cancelacion_por_Desenglobe'
  and rdcr.numero_predial is null
