--regla 2.32
with base_1 as (
	select cp.numero_predial
	, cp2.numero_documento 
	, cp2.tipo_persona 
	, case when cp2.tipo_persona = 'NATURAL' then 1 else 0 end p_natural 
	, case when cp2.tipo_persona = 'JURIDICA' then 1 else 0 end p_juridica
	, cp2.grupo_interesado 
	, count (cp.numero_predial) over (partition by cp.numero_predial) n_interesados
	, cp.coordinador
	, cp.usuario
	from {esquema}{punto}cica_predio cp 
	left join {esquema}{punto}cica_propietario cp2 on cp.numero_predial = cp2.numero_predial 
	where cp.estado = 'ACTIVO'
		and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')	
),
base_2 as (
	select 
	b.numero_predial
	, b.numero_documento
	, b.tipo_persona
	, b.grupo_interesado
	, b.coordinador
	, b.usuario
	, sum(p_natural) over (partition by b.numero_predial) int_naturales
	, sum(p_juridica) over (partition by b.numero_predial) int_juridicas
	from base_1 b
)
select distinct 
b.numero_predial
, b.numero_documento
, b.tipo_persona
, b.grupo_interesado
, b.int_naturales
, b.int_juridicas
, b.coordinador
, b.usuario as reconocedor
, 'Fail' cond_2_32
from base_2 b
where b.int_naturales >= 2
and b.int_juridicas = 0
and nullif(b.grupo_interesado,'') <> 'Grupo_Civil'
order by b.numero_predial