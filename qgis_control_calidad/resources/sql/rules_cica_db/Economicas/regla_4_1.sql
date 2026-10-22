--regla 4.1
select 
cuc.numero_predial 
,cuc.tipo_construccion 
,cuc.tipologia_id 
,cuc.tipologia_id_movil
,cuc.nombre 
,nullif(cuc.puntos,'') puntos
, cp.coordinador
, cp.usuario as reconocedor
,'Fail' as "4_1"  
from {esquema}{punto}cica_unidad_construccion cuc 
left join {esquema}{punto}cica_predio cp on cuc.numero_predial = cp.numero_predial 
where cuc.tipo_construccion = 'CONVENCIONAL'
and ((nullif(cuc.puntos,'')::numeric  = 0 or coalesce(regexp_replace(trim(cuc.puntos), '\s+', ' ', 'g'),'')='')) and (cuc.tipologia_id is null or cuc.tipologia_id ='')
and cp.estado = 'ACTIVO'
  and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')