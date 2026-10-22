--regla 1.24
select cp.numero_predial 
, cp.condicion_predio_tipo 
, cp.estado 
, coalesce (utc.codigo , '') 
|| coalesce(uti.codigo , '')
|| coalesce(rtc.codigo , '')
|| coalesce(rti.codigo , '') codigo_geo
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_1_24
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto}u_terreno_ctm12 utc on utc.codigo = cp.numero_predial 
left join {esquema}{punto}u_terreno_informal uti on uti.codigo = cp.numero_predial 
left join {esquema}{punto}r_terreno_ctm12 rtc on rtc.codigo = cp.numero_predial 
left join {esquema}{punto}r_terreno_informal rti on rti.codigo = cp.numero_predial 
where cp.condicion_predio_tipo in ('NPH', 'Matriz', 'Condominio.Matriz', 'Condominio.Unidad_Predial')
and cp.estado <> 'CANCELADO' 
and coalesce (utc.codigo , '') 
|| coalesce(uti.codigo , '')
|| coalesce(rtc.codigo , '')
|| coalesce(rti.codigo , '') = ''
and numero_predial in (
select numero_predial 
from {esquema}{punto}cica_predio cp
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)