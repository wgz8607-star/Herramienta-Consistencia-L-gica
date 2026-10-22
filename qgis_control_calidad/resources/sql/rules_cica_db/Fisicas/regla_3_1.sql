--regla 3.1
select cp.numero_predial 
, cp.condicion_predio_tipo 
, coalesce (uuc.codigo, '')|| coalesce (ruc.codigo,'') unidad
, cuc.uso
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_3_1
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto}u_unidad_ctm12 uuc on cp.numero_predial = uuc.codigo 
left join {esquema}{punto}r_unidad_ctm12 ruc on cp.numero_predial = ruc.codigo 
left join {esquema}{punto}cica_unidad_construccion cuc on cuc.numero_predial = cp.numero_predial 
where cp.condicion_predio_tipo = 'PH.Unidad'
and coalesce (uuc.codigo, '')|| coalesce (ruc.codigo,'') = ''
and coalesce(cuc.uso,'') not ilike '%PARQUEADERO%' 
and coalesce(cuc.uso,'') not ilike '%GARAJE%' 
and coalesce(cuc.uso,'') not ilike '%PH%NO%CONST%'
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')