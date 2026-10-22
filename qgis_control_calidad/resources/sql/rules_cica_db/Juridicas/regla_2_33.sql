--regla 2.33
with base_1 as (
	select cp.numero_predial
	, cp2.numero_documento 
	, cp2.tipo_persona 
	, case when cp2.tipo_persona = 'NATURAL' then 1 else 0 end p_natural 
	, case when cp2.tipo_persona = 'JUTIDICA' then 1 else 0 end p_juridica
	, cp2.grupo_interesado
	, cp.coordinador
	, cp.usuario
	, count (cp.numero_predial) over (partition by cp.numero_predial) n_interesados
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
, 'Fail' cond_2_33
from base_2 b
where b.int_naturales = 0
and b.int_juridicas >= 2
and nullif(b.grupo_interesado,'') <> 'Grupo_Empresarial'
order by b.numero_predial