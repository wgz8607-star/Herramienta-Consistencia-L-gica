--cond 1_29
with tb_cond_1_29_1 as (
select 
lp.t_id 
,lp.numero_predial_nacional
,ld.numero_torres
from {esquema}{punto}ilc_predio lp
left join {esquema}{punto}cr_datosphcondominio ld on ld.ilc_predio =lp.t_id
where substring(lp.numero_predial_nacional,22,9)='900000000' 
),
predios_asociados as (
select 
lp.numero_predial_nacional predio_matriz, 
lp.t_id tid_matriz, 
lp2.numero_predial_nacional numero_predial_nacional_unidad,
lpc.unidad_predial  tid_unidad_predial,
max(substring(lp2.numero_predial_nacional,23,2)) over (partition by lp.t_id) torre
from {esquema}{punto}ilc_predio lp
inner join tb_cond_1_29_1 tt on tt.t_id=lp.t_id
left join {esquema}{punto}cr_predio_copropiedad lpc on lpc.matriz =lp.t_id 
left join {esquema}{punto}ilc_predio lp2 on lp2.t_id =lpc.unidad_predial 
),
tb_final as(
select 
tb1.numero_predial_nacional, 
tb1.numero_torres,
max(pa.torre) max_torre
from tb_cond_1_29_1 tb1
left join predios_asociados pa on tb1.t_id=pa.tid_matriz
group by tb1.numero_predial_nacional, 
tb1.numero_torres
),
validacion as
(select 
numero_predial_nacional matriz,
numero_torres,
max_torre, 
case when numero_torres is null or max_torre is null then 'Fail' 
	when numero_torres = max_torre::int then 'OK' else 'Fail' end as cond_1_29 from tb_final
	)
select *
from validacion
where validacion.cond_1_29 = 'Fail'