--regla 3.22
with base as (
select 
cp.numero_predial 
, cp.area_construido 
, cp.destino 
, cuc.nombre
, cuc.unidad
, cuc.construccion_area::numeric u_const_area
, cp.coordinador
, cp.usuario
, case when cuc.nombre in (
  	'Industrial.Bodega_Casa_Bomba'
 , 'Industrial.Industrias'
 , 'Industrial.Industrias_en_PH'
 , 'Industrial.Talleres'
 , 'Industrial.Bodegas_Casa_Bomba_en_PH'
 , 'Anexos.Ramadas_Cobertizos_Caneyes'
	) then cuc.construccion_area::numeric else 0 end area_valida
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto}cica_unidad_construccion cuc on cuc.numero_predial = cp.numero_predial 
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
and cp.destino = 'B'
),
base2 as(
select 
b.numero_predial
, b.area_construido
, b.destino
, b.nombre
, b.unidad
, b.u_const_area
, b.area_valida
, b.coordinador
, b.usuario
, sum (b.area_valida) over (partition by b.numero_predial) suma_areas_validas
, sum (b.u_const_area) over (partition by b.numero_predial) suma_areas_u_const
from base b
)
select distinct 
b2.numero_predial
, b2.area_construido
, b2.destino
, b2.nombre
, b2.unidad
, b2.u_const_area
, b2.area_valida
, b2.suma_areas_validas
, b2.suma_areas_u_const
, b2.coordinador
, b2.usuario as reconocedor
, 'Fail' cond_3_20
from base2 b2
where b2.suma_areas_validas / (suma_areas_u_const+0.1) < 0.5
order by b2.numero_predial, b2.unidad