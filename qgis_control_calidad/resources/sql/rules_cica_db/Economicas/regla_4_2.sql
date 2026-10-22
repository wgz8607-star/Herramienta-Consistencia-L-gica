-- regla 4.2
select 
	cuc.numero_predial 
  , cuc.tipo_construccion 
  , cuc.tipo_calificacion 
  , cuc.calificacion_anexo_id
  , cuc.uso 
, cuc.puntos 
, cp.coordinador
, cp.usuario as reconocedor
from {esquema}{punto}cica_unidad_construccion cuc 
left join {esquema}{punto}cica_predio cp on cuc.numero_predial = cp.numero_predial
WHERE
tipo_calificacion = 'ANEXO' and
(
	(lower(cuc.nombre) in ('camaroneras','fuertes y castillos','murallas','torres de enfriamiento') and
	 puntos not in ('0')
	)
	or (
		lower(cuc.nombre) in ('lagunas de oxidación') and
		puntos not in ('20')
	) 
	or (
		lower(cuc.nombre) in ('canchas de tenis') and 
		puntos not in('10','20')
	)
	or (
		lower(cuc.nombre) in ('galpones - gallineros','establos – pesebreras – caballerizas','cocheras – marraneras – porquerizas','tanques','kioscos','corrales','marquesinas – patios cubiertos','cimientos, estructura, muros y placa base') and
		puntos not in ('20','40','60','80')
	)
	or (
		lower(cuc.nombre) in ('piscinas','toboganes') and 
		puntos not in ('40','50','60','80')
	)
	or(
		lower(cuc.nombre) in ('carretera') and 
		puntos not in ('40','60')
	)
	or(
		lower(cuc.nombre) in ('beneficiaderos','secaderos','pozos','albercas - bañaderas' ,'muelles') and 
		puntos not in ('40','60','80')
	)
	or(
		lower(cuc.nombre) in ('ramadas - cobertizos - caneyes') and
		puntos not in ('40','60','80','90')
	)
	or(
		lower(cuc.nombre) in ('silos','vía férrea') and
		puntos not in ('60','80')
	)
)
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')