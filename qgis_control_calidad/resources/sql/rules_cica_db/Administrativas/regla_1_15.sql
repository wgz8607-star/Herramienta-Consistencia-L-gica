--regla 1.15
select distinct
cp.numero_predial 
, cp.circulo_registral 
, cp.coordinador
, cp.usuario as reconocedor 
, 'Fail' cond_1_15
from {esquema}{punto}cica_predio cp 
where length(nullif(circulo_registral, ''))<>3
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')