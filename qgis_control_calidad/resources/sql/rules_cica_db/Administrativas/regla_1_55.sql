--regla 1.55
select cc.numero_predial 
, cc.direccion
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_55
from {esquema}{punto}cica_contacto cc 
left join {esquema}{punto}cica_predio cp on cc.numero_predial = cp.numero_predial 
where NULLIF(cc.direccion,'') is NULL
and cp.estado = 'ACTIVO'
	and cc.resultado_visita = 'Exitoso'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')