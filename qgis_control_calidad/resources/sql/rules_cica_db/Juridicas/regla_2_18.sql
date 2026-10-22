--regla 2.18
SELECT cp.numero_predial
, cp.tiene_fmi
,to_timestamp(jsr.fecha_documento,'MM-DD-YYYY')::date fecha_documento
,jsr.tipo_documento 
,jsr.numero_fuente 
,jsr.ente_emisor 
,to_timestamp(cc.fecha_visita,'MM-DD-YYYY')::date fecha_visita
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' as "2.18"
FROM {esquema}{punto}cica_predio cp
inner JOIN {esquema}{punto}cica_justificacion  jsr  ON cp.numero_predial = jsr.numero_predial
inner join {esquema}{punto}cica_contacto cc on cp.numero_predial = cc.numero_predial 
WHERE cp.tiene_fmi = 'SI' 
AND 
	(nullif(jsr.fecha_documento,'') IS NULL 
    OR nullif(jsr.tipo_documento,'') is null
   	or nullif(jsr.numero_fuente,'') is null
    or nullif(jsr.ente_emisor,'') is null
	or to_timestamp(jsr.fecha_documento,'MM-DD-YYYY') > to_timestamp(cc.fecha_visita,'MM-DD-YYYY') )
and cp.numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
