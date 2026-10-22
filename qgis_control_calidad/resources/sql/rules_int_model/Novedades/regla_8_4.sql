-- Regla 8.4: Cuando la novedad es Desenglobe por venta parcial: un predio debe conservar su NPN (npn = npn_novedad) con tipo Desenglobe_Venta_Parcial; los demás deben ser nuevos provisionales (pos18 ~ [A-Z9]).
-- Falla cuando: no existe predio con npn = npn_novedad y tipo Desenglobe_Venta_Parcial, el npn_novedad no existe en ilc_predio, faltan predios provisionales, o el predio tiene Cancelacion_por_Desenglobe en lugar de Desenglobe_Venta_Parcial.
-- Excepciones: ninguna.

-- Paso 1: todos los npn_novedad que participan en al menos un Desenglobe_Venta_Parcial
with dvp_keys as (
	select distinct ie.numero_predial npn_novedad
	from {esquema}{punto}ilc_predio ip
	join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
	join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
	join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
	where ietn.ilicode = 'Desenglobe_Venta_Parcial'
)
-- Paso 2: para cada npn_novedad, todos los predios (cualquier tipo) que lo referencian
,predios_asociados as (
	select distinct ip2.numero_predial_nacional npn
	, ie2.numero_predial npn_novedad
	, ietn2.ilicode tiponovedad
	from dvp_keys dk
	join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id2 on true
	join {esquema}{punto}ilc_predio ip2 on ip2.t_id = id2.ilc_predio
	join {esquema}{punto}ilc_estructuranovedadnumeropredial ie2 on ie2.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id2.t_id
	join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn2 on ietn2.t_id = ie2.tipo_novedad
	where ie2.numero_predial = dk.npn_novedad
)
,cond_8_4 as (
	select npn
	,npn_novedad
	,tiponovedad
	-- valid_1: predio conservado (npn = npn_novedad y tipo Desenglobe_Venta_Parcial)
	,case when npn = npn_novedad and tiponovedad = 'Desenglobe_Venta_Parcial' then 1 else 0 end as valid_1
	-- valid_2: predio nuevo provisional con tipo Desenglobe_Venta_Parcial
	,case when npn <> npn_novedad and substring(npn,18,1) ~ '[9A-Za-z]' and tiponovedad = 'Desenglobe_Venta_Parcial' then 1
	      when npn <> npn_novedad and tiponovedad = 'Desenglobe_Venta_Parcial' then 0
	      else null end as valid_2
	,count(npn_novedad) over (partition by npn_novedad) conteo_novedad
	from predios_asociados
)
,npn_novedades_error as (
	select
	npn_novedad
	,conteo_novedad
	, case when sum(valid_1) > 1 then 'Fail - exceso de coincidencias'
	       when sum(valid_1) < 1 then 'Fail - No hay coincidencias o tipo incorrecto'
	       when sum(valid_1) = 1 then 'Ok' else 'Fail' end valid_npn_iguales
	, case when sum(coalesce(valid_2,0)) < 1 then 'Fail' else 'Ok' end valid_npn_pos18
	, case when conteo_novedad < 2 then 'Fail - novedades insuficientes' else 'Ok' end conteo_novedades
	from cond_8_4
	group by npn_novedad, conteo_novedad
)
-- Rama A: estructura inválida para grupos cuyo npn_novedad sí existe en ilc_predio
select distinct
ip.numero_predial_nacional
,nne.npn_novedad
,ietn.ilicode tiponovedad
,nne.conteo_novedades
,nne.valid_npn_iguales
,nne.valid_npn_pos18
,'Fail' cond_8_4
from npn_novedades_error nne
join {esquema}{punto}ilc_predio ip on exists (
	select 1
	from {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id2
	join {esquema}{punto}ilc_estructuranovedadnumeropredial ie2 on ie2.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id2.t_id
	where id2.ilc_predio = ip.t_id
	and ie2.numero_predial = nne.npn_novedad
)
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
where ie.numero_predial = nne.npn_novedad
  and (valid_npn_iguales <> 'Ok'
    or valid_npn_pos18 <> 'Ok'
    or conteo_novedades <> 'Ok')

union all

-- Rama B: npn_novedad no existe en ilc_predio (predio que debería conservarse está ausente)
select
pa.npn as numero_predial_nacional
,pa.npn_novedad
,pa.tiponovedad
,'Fail - npn_novedad no existe en ilc_predio' as conteo_novedades
,null as valid_npn_iguales
,null as valid_npn_pos18
,'Fail' cond_8_4
from predios_asociados pa
where pa.npn_novedad not in (select numero_predial_nacional from {esquema}{punto}ilc_predio)

order by npn_novedad
