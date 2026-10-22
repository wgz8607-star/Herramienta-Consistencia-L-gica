--regla 3.3
select cp.numero_predial 
, cp.condicion_predio_tipo
, cuc.tipo_calificacion 
, cuc.nombre 
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_3_3
from {esquema}{punto}cica_predio cp 
full join {esquema}{punto}cica_unidad_construccion cuc on cuc.numero_predial = cp.numero_predial 
where cp.condicion_predio_tipo in ('PH', 'Condominio')
and upper(cuc.tipo_calificacion) in ('RESIDENCIAL', 'COMERCIAL', 'INSTITUCIONAL', 'INDUSTRIAL')
and cuc.nombre not ilike '%PH'
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')