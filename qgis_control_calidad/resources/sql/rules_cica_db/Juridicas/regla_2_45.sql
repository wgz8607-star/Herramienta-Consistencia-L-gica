--regla_2_45
with predio_derecho as(
select ip.numero_predial, 
substring(ip.numero_predial,22,1)::numeric as dig_22,
id.tipo_derecho,
ip.condicion_predio_tipo as condicion,
ip.estado,
ip.etapa,
ip.coordinador as coord, 
ip.usuario as reconocedor
from {esquema}{punto}cica_predio ip
left join {esquema}{punto}cica_predio_derecho id on id.numero_predial=ip.numero_predial
where ip.estado='ACTIVO' and ip.etapa in ('CONTROL_CALIDAD_GENERAL','CONTROL_CALIDAD_GRUPO')
),
predio_k as (
select 
t.numero_predial,
t.dig_22,
t.tipo_derecho,
t.condicion,
case when (t.dig_22 in ('0','3','4','7','8','9') and t.tipo_derecho <> 'Dominio')
	or (t.dig_22 in (2) and t.tipo_derecho not in ('Ocupación','Posesión'))
	then 'FAIL' else 'OK' end igualdad
from predio_derecho t
)
select
k.numero_predial,
k.dig_22,
k.tipo_derecho,
k.condicion,
cp.coordinador,
cp.usuario as reconocedor,
k.igualdad as regla_2_45
from predio_k k
left join {esquema}{punto}cica_predio cp on cp.numero_predial = k.numero_predial
where k.igualdad ='FAIL';