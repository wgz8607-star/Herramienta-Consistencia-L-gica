--regla 1.7
select cp.numero_predial 
, cp.condicion_predio_tipo 
, cp.condicion_predio
, cp.coordinador 
, cp.usuario as reconocedor
, 'Fail' cond_1_7
from {esquema}{punto}cica_predio cp 
where cp.condicion_predio_tipo = 'Condominio.Unidad_Predial' and (
	substring(cp.numero_predial, 22, 5) <> '80000'
	or substring(cp.numero_predial, 27, 4) = '0000')
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)