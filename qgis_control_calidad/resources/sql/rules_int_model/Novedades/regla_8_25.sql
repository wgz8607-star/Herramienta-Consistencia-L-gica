-- Regla 8.25: Para novedades de englobe, desenglobe o predio nuevo: el npn_novedad no puede estar vinculado simultáneamente a Predio_Nuevo y a otra novedad de englobe/desenglobe en el mismo predio.
-- Falla cuando: la combinación de novedades por npn_novedad no corresponde a ninguna estructura válida, o un predio tiene Predio_Nuevo y además Desenglobe/Englobe.
with tb1 as(
select
--ip.numero_predial_nacional,
ie.numero_predial numero_predial,
ietn.ilicode as tipo_novedad,
case when ietn.ilicode like 'Englobe%' then 1 else 0 end as englobe,
case when ietn.ilicode like 'Desenglobe%' then 1 else 0 end as desenglobe,
case when ietn.ilicode like 'Cancelacion%' then 1 else 0 end as cancelacion,
case when ietn.ilicode like 'Predio_Nuevo%' then 1 else 0 end as predionuevo
from {esquema}{punto}ilc_estructuranovedadnumeropredial ie
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.t_id=ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales
left join {esquema}{punto}ilc_predio ip on ip.t_id=id.ilc_predio
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
where ietn.ilicode in ('Desenglobe_Venta_Parcial','Desenglobe_Division_Material','Englobe_Nuevo_FMI','Englobe_Mantiene_FMI','Cancelacion_por_Englobe','Cancelacion_por_Desenglobe','Predio_Nuevo')
), sumas as (
select
t.numero_predial
,string_agg(distinct tipo_novedad, ',' order by tipo_novedad) as tipo_novedades
, sum(englobe) englobes
, sum (desenglobe) desenglobles
, sum (cancelacion) cancelaciones
,sum (predionuevo) prediosnuevos
--,'Fail' cond_8_25
 from tb1 t
group by numero_predial
), comparaciones as (
select
s.numero_predial,
s.tipo_novedades,
s.englobes,
s.desenglobles,
s.cancelaciones,
s.prediosnuevos,
case when s.tipo_novedades='Predio_Nuevo'
       and englobes=0
         and desenglobles=0
           and cancelaciones=0
            and prediosnuevos=1
     then 'OK'
    else 'FAIL'
end comparacion    
from sumas s
where s.tipo_novedades like '%Predio_Nuevo%'
union all
select
s.numero_predial,
s.tipo_novedades,
s.englobes,
s.desenglobles,
s.cancelaciones,
s.prediosnuevos,
case when s.tipo_novedades='Cancelacion_por_Desenglobe,Desenglobe_Division_Material'
       and englobes=0
         and desenglobles>1
           and cancelaciones=1
            and prediosnuevos=0
     then 'OK'
    else 'FAIL'
end comparacion    
from sumas s
where s.tipo_novedades = 'Cancelacion_por_Desenglobe,Desenglobe_Division_Material'
union all
select
s.numero_predial,
s.tipo_novedades,
s.englobes,
s.desenglobles,
s.cancelaciones,
s.prediosnuevos,
case when s.tipo_novedades='Cancelacion_por_Englobe,Englobe_Nuevo_FMI'
       and englobes>1
         and desenglobles=0
           and cancelaciones=1
            and prediosnuevos=0
     then 'OK'      
    else 'FAIL'
end comparacion    
from sumas s
where s.tipo_novedades in ('Englobe_Nuevo_FMI','Cancelacion_por_Englobe')
union all
select
s.numero_predial,
s.tipo_novedades,
s.englobes,
s.desenglobles,
s.cancelaciones,
s.prediosnuevos,
case when s.tipo_novedades ='Cancelacion_por_Englobe,Englobe_Mantiene_FMI'
       and englobes>1
         and desenglobles=0
           and cancelaciones=1
            and prediosnuevos=0
     then 'OK'
      when   s.tipo_novedades = 'Englobe_Mantiene_FMI'
       and englobes>1
         and desenglobles=0
           and cancelaciones=0
            and prediosnuevos=0
             and ip.numero_predial_nacional=numero_predial
     then 'OK'
    else 'FAIL'
end comparacion    
from sumas s
left join {esquema}{punto}ilc_predio ip on ip.numero_predial_nacional=numero_predial 
where s.tipo_novedades in ('Englobe_Mantiene_FMI','Cancelacion_por_Englobe')
)
-- CTE extra: predios que tienen Predio_Nuevo Y alguna novedad de Desenglobe/Englobe en el mismo predio
-- (el agrupamiento en sumas es por ie.numero_predial, no por predio, así que esto no se detecta arriba)
,predio_nuevo_mixto as (
	select
	ip.numero_predial_nacional as numero_predial
	,string_agg(distinct ietn.ilicode, ',' order by ietn.ilicode) as tipo_novedades
	,sum(case when ietn.ilicode like 'Englobe%' then 1 else 0 end) as englobes
	,sum(case when ietn.ilicode like 'Desenglobe%' then 1 else 0 end) as desenglobles
	,sum(case when ietn.ilicode like 'Cancelacion%' then 1 else 0 end) as cancelaciones
	,sum(case when ietn.ilicode = 'Predio_Nuevo' then 1 else 0 end) as prediosnuevos
	,'FAIL' as comparacion
	from {esquema}{punto}ilc_predio ip
	join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
	join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
	join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
	where ietn.ilicode in ('Desenglobe_Venta_Parcial','Desenglobe_Division_Material','Englobe_Nuevo_FMI','Englobe_Mantiene_FMI','Predio_Nuevo')
	group by ip.t_id, ip.numero_predial_nacional
	having
	  bool_or(ietn.ilicode = 'Predio_Nuevo')
	  and bool_or(ietn.ilicode in ('Desenglobe_Venta_Parcial','Desenglobe_Division_Material','Englobe_Nuevo_FMI','Englobe_Mantiene_FMI'))
)
select distinct
*,
'Fail' cond_8_25
from comparaciones s
where S.comparacion='FAIL'

union all

select
*,
'Fail' cond_8_25
from predio_nuevo_mixto

order by numero_predial
