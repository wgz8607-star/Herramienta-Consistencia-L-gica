--regla 1.54
select cc.numero_predial 
, cc.autorizacion_notificacion  
, cc.celular 
, cc.correo_electronico 
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_54
from {esquema}{punto}cica_contacto cc 
left join {esquema}{punto}cica_predio cp on cc.numero_predial = cp.numero_predial 
where cc.autorizacion_notificacion = 'SI' 
and NULLIF(cc.correo_electronico,'') is null
and NULLIF(cc.celular,'') is NULL
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')