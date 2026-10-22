-- Regla 8.5: Para novedad de Desenglobe_Division_Material: el predio origen debe quedar cancelado (Cancelacion_por_Desenglobe) y los predios resultantes deben ser nuevos provisionales (pos18 ~ [A-Z9]).
-- Falla cuando: no hay predio cancelado con npn = npn_novedad, los nuevos no son provisionales, o el npn_novedad no existe en ilc_predio.
-- Excepciones: ninguna.
with desenglobes as(
	select ip.numero_predial_nacional npn_predio
	,ie.numero_predial npn_novedad
	,ietn.ilicode tipo_novedad
	from {esquema}{punto}ilc_predio ip
	left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
	left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
	left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
	where ietn.ilicode in ('Cancelacion_por_Desenglobe', 'Desenglobe_Division_Material')
	order by ie.numero_predial
)
,predios_asociados as (
	select distinct ip2.numero_predial_nacional npn
	, ie.numero_predial npn_novedad
	, rdcr.numero_predial npn_r1
	, ietn.ilicode tiponovedad
	from desenglobes, {esquema}{punto}ilc_predio ip2
	left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip2.t_id
	left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
	inner join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
	left join {esquema_r1}.{tabla_r1} rdcr on rdcr.numero_predial = ip2.numero_predial_nacional
	where ie.numero_predial in (desenglobes.npn_novedad) order by ie.numero_predial
)

--select *
--from predios_asociados
,cond_8_5 as (
	select npn
	,npn_novedad
	,npn_r1
	,tiponovedad
	,case when (npn = npn_r1 and tiponovedad='Cancelacion_por_Desenglobe') then 1
	      when (npn <> npn_r1 and tiponovedad='Cancelacion_por_Desenglobe') then 0
	      else null
	        end as valid_1
	,case when (substring(npn,18,1)~'[9A-Za-z]' and tiponovedad='Desenglobe_Division_Material') then 1
	        when (substring(npn,18,1)!~'[9A-Za-z]' and tiponovedad='Desenglobe_Division_Material') then 0
	       else null
	         end as valid_2
	,count(npn_novedad) over (partition by npn_novedad) conteo_novedad
	from predios_asociados
)
--select *
--from cond_8_5
,npn_novedades_error as (
	select
	npn_novedad
	,max(npn_r1) as npn_r1   -- R1 del predio cancelado; NULL en las filas DDM por eso se usa MAX
	,conteo_novedad
	, case when sum(valid_1) > 1 then 'Fail - exceso de coincidencias'
	       when sum(valid_1) = 1 then 'Ok'
	       else 'Fail' end valid_npn_iguales
	, case when sum(valid_2) < 1 then 'Fail' else 'Ok' end valid_npn_pos18
	, case when avg(coalesce(conteo_novedad,0)) <> sum(coalesce(valid_2,0)) + sum(coalesce(valid_1,0)) then 'Fail' else 'Ok' end coherencia_novedades
	, case when conteo_novedad < 3 then 'Fail - novedades insuficientes' else 'Ok' end conteo_novedades
	from cond_8_5
	group by npn_novedad, conteo_novedad
)
, error as (
	select *,
	case when valid_npn_iguales = 'Ok' and valid_npn_pos18 = 'Ok'
	     and coherencia_novedades = 'Ok' and conteo_novedades = 'Ok'
	then 'OK'
	else 'FAIL'
	end error
	from npn_novedades_error
)
--select *
--from error

-- Rama A: npn_novedad existe en ilc_predio pero tiene errores de estructura
select
ip.numero_predial_nacional
,nne.npn_novedad
,nne.npn_r1
,null as tiponovedad
,nne.conteo_novedades
,nne.valid_npn_iguales
,nne.valid_npn_pos18
,nne.coherencia_novedades
,'Fail' cond_8_5
from error nne
left join {esquema}{punto}ilc_predio ip on ip.numero_predial_nacional = nne.npn_novedad
where nne.error = 'FAIL'
  and ip.numero_predial_nacional is not null

union all

-- Rama B: npn_novedad no existe en ilc_predio (se muestra cada predio DDM afectado)
select
d.npn_predio as numero_predial_nacional
,d.npn_novedad
,rdcr2.numero_predial as npn_r1
,'Fail - predio origen no existe en ilc_predio con Cancelacion_por_Desenglobe' as tiponovedad
,null as conteo_novedades
,null as valid_npn_iguales
,null as valid_npn_pos18
,null as coherencia_novedades
,'Fail' cond_8_5
from desenglobes d
left join {esquema_r1}.{tabla_r1} rdcr2 on rdcr2.numero_predial = d.npn_novedad
where d.tipo_novedad = 'Desenglobe_Division_Material'
  and not exists (
	select 1 from predios_asociados pa
	where pa.npn_novedad = d.npn_novedad
	and pa.tiponovedad = 'Cancelacion_por_Desenglobe'
	and pa.npn = d.npn_novedad
  )
order by npn_novedad
