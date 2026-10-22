--regla 1.50
select cc.numero_predial 
, cc.numero_documento 
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_50
from {esquema}{punto}cica_contacto cc 
left join {esquema}{punto}cica_predio cp on cp.numero_predial = cc.numero_predial 
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
and (nullif(cc.numero_documento,'') !~ '^[0-9]+$' OR cc.numero_documento LIKE '00%')
and cc.resultado_visita = 'Exitoso'