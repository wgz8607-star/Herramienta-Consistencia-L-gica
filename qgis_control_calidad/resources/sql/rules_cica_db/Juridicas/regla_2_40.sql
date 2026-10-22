    
with datos as ( 
select 
distinct
cp.numero_documento  
, cp.nombre1 
, cp.nombre2 
, cp.apellido1 
, cp.apellido2 
, cp.razon_social 
from {esquema}{punto}cica_propietario cp 
left join {esquema}{punto}cica_predio cp2 on cp.numero_predial = cp2.numero_predial
where CP.estado = 'ACTIVO'
and cp2.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
, resumen as (
select *, count (datos.numero_documento) over (partition by datos.numero_documento) conteo
from datos
where length(numero_documento)>4
)
, propietario_npn as (
select distinct
r.*, cp.numero_predial 
from resumen r
left join {esquema}{punto}cica_propietario cp on cp.numero_documento = r.numero_documento
	and cp.nombre1 = r.nombre1
	and cp.nombre2 = r.nombre2
	and cp.apellido1 = r.apellido1
	and cp.apellido2 = r.apellido2
	and cp.razon_social = r.razon_social
	and cp.estado = 'ACTIVO'
where conteo >1
order by r.numero_documento
)
select 
distinct
cp.numero_predial 
, cp2.estado 
, cp2.etapa
, pn.numero_documento
, pn.conteo
, pn.nombre1 
, pn.nombre2 
, pn.apellido1 
, pn.apellido2 
, pn.razon_social 
, cp2.coordinador as coordinador 
, cp2.usuario as reconocedor 
from propietario_npn pn
left join {esquema}{punto}cica_propietario cp on cp.numero_predial = pn.numero_predial
left join {esquema}{punto}cica_predio cp2 on cp2.numero_predial = cp.numero_predial 
where cp2.estado = 'ACTIVO'
and length(pn.numero_documento) >4
and cp2.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
order by pn.numero_documento
