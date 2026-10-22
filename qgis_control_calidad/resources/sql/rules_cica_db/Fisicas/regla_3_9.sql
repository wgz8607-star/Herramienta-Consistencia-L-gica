--regla 3.9
with tb1 as (
select cuc.numero_predial 
, cuc.unidad 
, ascii(cuc.unidad )-64 consecutivo
, row_number () over (partition by cuc.numero_predial order by cuc.numero_predial, cuc.unidad) fila
, cuc.tipo_dominio 
, cuc.tipo_planta 
, cuc.uso 
, cuc.anio_construccion 
, cp.coordinador
, cp.usuario as reconocedor
from {esquema}{punto}cica_unidad_construccion cuc 
left join {esquema}{punto}cica_predio cp on cuc.numero_predial = cp.numero_predial
order by cuc.numero_predial, cuc.unidad
)
,tb2 as (
select numero_predial ,unidad, consecutivo, fila, tipo_dominio, uso, anio_construccion, 'Fail' cond_3_9 
from tb1
where consecutivo <> fila
)
select *, 'Fail' cond_3_9 from tb1 where tb1.numero_predial in (select distinct numero_predial from tb2 )
and numero_predial in (
	select numero_predial 
	from {esquema}{punto}cica_predio cp
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)