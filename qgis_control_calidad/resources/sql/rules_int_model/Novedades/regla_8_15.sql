-- Regla 8.15: Un mismo npn_novedad no puede estar asociado a novedades de tipos incompatibles (ej. Cambio_... y Desenglobe_...).
-- Falla cuando: un numero_predial en ilc_estructuranovedadnumeropredial aparece vinculado a más de un tipo de novedad, o el predio fuente y destino de un Cambio son el mismo.
-- Excepciones: ninguna.

-- CTE auxiliar: todas las novedades agrupadas por npn_novedad (para mostrar contexto completo)
with todas_novedades_por_npn as (
	select
	ie3.numero_predial
	,string_agg(distinct ietn3.ilicode, ', ' order by ietn3.ilicode) as novedades_asociadas
	from {esquema}{punto}ilc_estructuranovedadnumeropredial ie3
	left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn3 on ietn3.t_id = ie3.tipo_novedad
	group by ie3.numero_predial
)
,cond_8_15 as (
	select ip.numero_predial_nacional npn
	, ietn.ilicode tiponovedad
	, ie.numero_predial npn_novedad
	from {esquema}{punto}ilc_predio ip
	left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
	left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
	left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
)
-- Rama A: predios Cambio donde fuente = destino o el destino existe en ilc_predio con el mismo tipo
select
c.npn as predio_origen
,c.tiponovedad
,c.npn_novedad
,ip.numero_predial_nacional as predio_destino
,tn.novedades_asociadas
,'Fail' cond_8_15
from cond_8_15 c
left join {esquema}{punto}ilc_predio ip on ip.numero_predial_nacional = c.npn_novedad
left join todas_novedades_por_npn tn on tn.numero_predial = c.npn_novedad
where split_part(c.tiponovedad,'_',1) = 'Cambio'
  and (c.npn = c.npn_novedad or c.npn_novedad = ip.numero_predial_nacional)

union all

-- Rama B: npn_novedad referenciado por más de un tipo de novedad (incompatibilidad)
select
ie2.numero_predial as predio_origen
,ietn2.ilicode as tiponovedad
,ie2.numero_predial as npn_novedad
,null as predio_destino
,tn2.novedades_asociadas
,'Fail' cond_8_15
from {esquema}{punto}ilc_estructuranovedadnumeropredial ie2
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn2 on ietn2.t_id = ie2.tipo_novedad
left join todas_novedades_por_npn tn2 on tn2.numero_predial = ie2.numero_predial
where split_part(ietn2.ilicode,'_',1) = 'Cambio'
  and ie2.numero_predial in (
	select numero_predial
	from {esquema}{punto}ilc_estructuranovedadnumeropredial
	group by numero_predial
	having count(*) > 1
  )
