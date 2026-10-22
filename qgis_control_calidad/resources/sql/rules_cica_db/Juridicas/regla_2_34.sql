--regla 2.34
select 
	jsr.numero_predial 
	,jsr.tipo_fuente 
	,jsr.tipo_documento
	, cp.coordinador
	, cp.usuario as reconocedor
	,'Fail' as "2.34"
from {esquema}{punto}cica_justificacion jsr
left join {esquema}{punto}cica_predio cp on jsr.numero_predial = cp.numero_predial 
where jsr.tipo_fuente = 'Documento_Privado' 
and (jsr.tipo_documento= 'Escritura_Publica' 
or jsr.tipo_documento= 'Sentencia_Judicial'
or jsr.tipo_documento= 'Acto_Administrativo')
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')