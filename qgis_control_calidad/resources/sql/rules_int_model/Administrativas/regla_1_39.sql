--regla 1.39
with cancelados as (
select ip.numero_predial_nacional npn
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio=ip.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id=ie.tipo_novedad
where ietn.ilicode like 'Cancelacion%'
)
,tb_base as(
select ip.numero_predial_nacional,
sum(case when e.t_id is null then 0 else 1 end) num_direcciones,
sum(case when e.es_direccion_principal =true then 1 else 0 end) num_direcciones_principales
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}extdireccion e on e.ilc_predio_direccion =ip.t_id
where ip.numero_predial_nacional not in (select npn from cancelados)
group by ip.numero_predial_nacional)
,tb_cond_1_39 as(
select *,
case when num_direcciones = 0 then 'Fail'
	 when num_direcciones >0 and num_direcciones_principales <> 1 then 'Fail'
	 when num_direcciones >0 and num_direcciones_principales =  1 then 'Ok'
	 else 'Fail' end as cond_1_39
from tb_base)
select * from tb_cond_1_39 where cond_1_39 ='Fail'
