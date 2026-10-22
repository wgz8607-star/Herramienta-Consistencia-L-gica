--regla 1.13
with base as (
select cp.numero_predial 
, cp.matricula 
, count(cp.matricula) over (partition by  cp.matricula) conteo_matricula
, cp.coordinador
, cp.usuario
from {esquema}{punto}cica_predio cp 
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
and nullif(cp.matricula,'') is not null
)
select distinct 
b.numero_predial
, b.matricula
, b.conteo_matricula
, b.coordinador
, b.usuario as reconocedor
, 'Fail' cond_1_13
from base b
where b.conteo_matricula > 1
order by b.matricula