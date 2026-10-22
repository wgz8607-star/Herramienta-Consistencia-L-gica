--regla 2.24
with tb1 as (
SELECT cp.numero_predial
,cdp.Tipo_Persona
,cdp.Nombre1
,cdp.Apellido1
,cdp.Nombre2
,cdp.Apellido2
,cdp.razon_social
,cp.estado
,cp.etapa
,cp.coordinador
,cp.usuario as reconocedor
, case when NULLIF(cdp.nombre1,'') is null or NULLIF(cdp.apellido1,'') is null or NULLIF(cdp.razon_social,'') is not null then 'Fail' 
	   when cdp.Nombre1 ~ '[^a-zA-Z\sÑñÁáÉéÍíÓóÚú ]' or cdp.Apellido1 ~ '[^a-zA-Z\sÑñÁáÉéÍíÓóÚú ]' then 'Fail'
	   when NULLIF(cdp.nombre2,'') is not null and cdp.Nombre2 ~ '[^a-zA-Z\sÑñÁáÉéÍíÓóÚú ]' then 'Fail'
	   when NULLIF(cdp.apellido2,'') is not null and cdp.apellido2 ~ '[^a-zA-Z\sÑñÁáÉéÍíÓóÚú ]' then 'Fail'
	   else 'Ok' end as  cond_2_24
FROM {esquema}{punto}cica_propietario cdp
left JOIN {esquema}{punto}cica_predio cp ON cdp.numero_predial  = cp.numero_predial
WHERE cdp.Tipo_Persona = 'NATURAL' /*and
 1=1 or (
        (cdp.Nombre1 ~ '[^a-zA-Z\sÑñÁáÉéÍíÓóÚú ]') OR 
        (cdp.Apellido1 ~ '[^a-zA-Z\sÑñÁáÉéÍíÓóÚú ]') OR
        ((cdp.Nombre2 IS NULL or cdp.Nombre2 ~ '[^a-zA-Z\sÑñÁáÉéÍíÓóÚú ]') OR 
        (cdp.Apellido2 IS NULL or cdp.Apellido2 ~ '[^a-zA-Z\sÑñÁáÉéÍíÓóÚú ]')))*/
)
select tb1.numero_predial
,tb1.Tipo_Persona
,tb1.Nombre1
,tb1.Apellido1
,tb1.Nombre2
,tb1.Apellido2
,tb1.razon_social
,tb1.coordinador
,reconocedor
,tb1.cond_2_24
from tb1 
where  cond_2_24 ='Fail' and tb1.estado = 'ACTIVO'
	and tb1.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')