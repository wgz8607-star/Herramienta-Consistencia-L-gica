--regla 1.53
select cc.numero_predial 
, cc.correo_electronico  
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_53
from {esquema}{punto}cica_contacto cc
left join {esquema}{punto}cica_predio cp on cc.numero_predial = cp.numero_predial 
where NULLIF(cc.correo_electronico,'')  !~ '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}])|(([a-zA-Z\u0400-\uffff\-0-9]+\.)+[a-zA-Z\u0400-\uffff]{{2,}}))$'
or NULLIF(cc.correo_electronico,'') ~ '[áéíóúÁÉÍÓÚ\+\*]'
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')