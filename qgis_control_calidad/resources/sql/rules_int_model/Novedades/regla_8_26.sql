-- Regla 8.26: Los predios involucrados en novedades deben pertenecer al mismo municipio.
-- Falla cuando: los NPNs de fuente y resultado tienen diferente código municipal.
with tb1 as(
select ie.numero_predial numero_predial, 
case when ietn.ilicode like 'Cancelacion%' then 1 else 0 end as cancelacion,
case when ietn.ilicode like 'Predio_Nuevo%' then 1 else 0 end as predionuevo
 from {esquema}{punto}ilc_estructuranovedadnumeropredial ie 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
),tb2 as (
select numero_predial
, sum (cancelacion) cancelaciones
,sum (predionuevo) prediosnuevos
,'Fail' cond_8_26
 from tb1
group by numero_predial
having sum(cancelacion) +  sum (predionuevo) > 1 
)
select *
from tb2 t
where (t.cancelaciones>0 and t.prediosnuevos>0)
