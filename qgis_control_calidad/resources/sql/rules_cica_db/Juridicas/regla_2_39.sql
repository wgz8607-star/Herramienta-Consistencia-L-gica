--regla 2.39
with base1 as (
	select cp.numero_predial 
	, cp2.nombre1 
	, cp2.nombre2 
	, cp2.apellido1 
	, cp2.apellido2 
	, cp2.razon_social 
	, cp2.numero_documento 
	, cp.coordinador
	, cp.usuario
	from {esquema}{punto}cica_propietario cp2
	left join {esquema}{punto}cica_predio cp on cp2.numero_predial = cp.numero_predial 
	where cp.estado = 'ACTIVO'
		and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
, base2 as (
	select distinct 
	b1.nombre1
	, b1.nombre2
	, b1.apellido1
	, b1.apellido2
	, b1.razon_social
	, b1.numero_documento
	from base1 b1
)
, base3 as(
	select b2.nombre1
	, b2.nombre2
	, b2.apellido1
	, b2.apellido2
	, b2.razon_social
	, b2.numero_documento
	, count(coalesce(b2.nombre1,'') || coalesce(b2.nombre2,'') || coalesce(b2.apellido1,'') || coalesce(b2.apellido2,'') || coalesce(b2.razon_social,'')) 
 	over (partition by coalesce(b2.nombre1,'') || coalesce(b2.nombre2,'') || coalesce(b2.apellido1,'') || coalesce(b2.apellido2,'') || coalesce(b2.razon_social,'')) conteo
	from base2 b2
)
select distinct
b1.numero_predial
, b3.nombre1
, b3.nombre2
, b3.apellido1
, b3.apellido2
, b3.razon_social
, b3.numero_documento
, b3.conteo
, b1.coordinador
, b1.usuario as reconocedor
, 'Fail' cond_2_39
from base3 b3
left join base1 b1 on 		coalesce(b1.nombre1,'') = coalesce(b3.nombre1,'')
						and coalesce(b1.nombre2,'') = coalesce(b3.nombre2,'')
						and coalesce(b1.apellido1,'') = coalesce(b3.apellido1,'')
						and coalesce(b1.apellido2,'') = coalesce(b3.apellido2,'')
						and coalesce(b1.razon_social,'') = coalesce(b3.razon_social,'')
						and coalesce(b1.numero_documento,'') = coalesce(b3.numero_documento,'')
where b3.conteo > 1
order by b3.nombre1
, b3.nombre2
, b3.apellido1
, b3.apellido2
, b3.razon_social