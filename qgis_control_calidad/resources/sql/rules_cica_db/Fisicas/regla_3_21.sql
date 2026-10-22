-- regla 3.21
with base as (
select 
cp.numero_predial 
, cp.area_construido 
, cp.destino 
, cuc.nombre
, cuc.unidad
, cp.coordinador
, cp.usuario
, NULLIF(cuc.construccion_area,'')::numeric u_const_area
, case when cuc.nombre in (
  	'Institucional.Colegio_y_Universidades',
'Institucional.Biblioteca',
'Comercial.Bodegas_Comerciales_Grandes_Almacenes',
'Institucional.Clinicas_Hospitales_Centros_Medicos',
'Comercial.Hoteles_en_PH',
'Comercial.Comercio',
'Institucional.Iglesia',
'Institucional.Casas_de_Culto',
'Comercial.Hoteles',
'Comercial.Clubes_Casinos',
'Comercial.Oficinas_Consultorios',
'Comercial.Restaurantes',
'Comercial.Pensiones_y_Residencias',
'Institucional.Puestos_de_Salud',
'Comercial.Parqueaderos',
'Comercial.Teatro_Cinemas',
'Institucional.Aulas_de_Clases',
'Institucional.Coliseos',
'Institucional.Casas_de_Culto',
'Institucional.Jardin_Infantil_en_Casa',
'Anexos.Estacion_Bombeo',
'Institucional.Plaza_de_Toros',
'Institucional.Carceles',
'Industrial.Bodega_Casa_Bomba',
'Industrial.Talleres',
'Institucional.Parque_Cementerios',
'Comercial.Comercio_Colonial',
'Comercial.Oficinas_Consultorios_Coloniales',
'Comercial.Centros_Comerciales',
'Comercial.Bodegas_Comerciales_en_PH',
'Comercial.Comercio_en_PH',
'Comercial.Centros_Comerciales_en_PH',
'Comercial.Oficinas_Consultorios_en_PH',
'Comercial.Parqueaderos_en_PH',
'Comercial.Teatro_Cinemas',
'Institucional.Iglesia_en_PH',
'Comercial.Restaurantes_en_PH',
'Comercial.Hotel_Colonial',
'Anexos.Ramadas_Cobertizos_Caneyes'
	) then NULLIF(cuc.construccion_area,'')::numeric else 0 end area_valida
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto}cica_unidad_construccion cuc on cuc.numero_predial = cp.numero_predial 
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
and cp.destino = 'C'
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