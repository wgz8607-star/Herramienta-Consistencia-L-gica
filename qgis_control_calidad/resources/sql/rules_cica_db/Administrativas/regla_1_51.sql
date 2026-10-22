--regla 1.51
select cc.numero_predial 
, cc.primer_nombre 
, cc.primer_apellido
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_51
from {esquema}{punto}cica_contacto cc 
left join {esquema}{punto}cica_predio cp on cc.numero_predial = cp.numero_predial 
where NULLIF(cc.primer_nombre, '') || NULLIF(cc.primer_apellido, '') is null 
and cp.estado = 'ACTIVO'
	and cc.resultado_visita = 'Exitoso'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')