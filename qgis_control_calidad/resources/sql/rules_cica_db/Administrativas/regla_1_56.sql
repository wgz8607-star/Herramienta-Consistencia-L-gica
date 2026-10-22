--regla 1.56
select cc.numero_predial 
, cc.direccion
, length(cc.direccion) largo_direccion
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_56
from {esquema}{punto}cica_contacto cc 
left join {esquema}{punto}cica_predio cp on cc.numero_predial = cp.numero_predial 
where length(NULLIF(cc.direccion,'')) < 7 
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')