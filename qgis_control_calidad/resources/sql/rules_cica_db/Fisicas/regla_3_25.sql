-- regla 3.25
select cuc.numero_predial 
, cuc.nombre
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_3_25
from {esquema}{punto}cica_unidad_construccion cuc 
left join {esquema}{punto}cica_predio cp on cuc.numero_predial = cp.numero_predial
where NULLIF(cuc.nombre,'') is NULL
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')