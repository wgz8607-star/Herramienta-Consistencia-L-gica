--regla 1.52
select cc.numero_predial 
, cc.celular 
, length(cc.celular) digitos_celular
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_52
from {esquema}{punto}cica_contacto cc 
left join {esquema}{punto}cica_predio cp on cc.numero_predial = cp.numero_predial 
where NULLIF(cc.celular,'') !~ '^\d{{10}}$'
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')