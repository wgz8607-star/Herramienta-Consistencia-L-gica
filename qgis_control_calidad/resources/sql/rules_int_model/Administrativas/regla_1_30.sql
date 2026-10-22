--cond 1_30--cond 1_30--cond 1_30
with tb_cond_1_30_1 as (
select 
lp.t_id 
,lp.numero_predial_nacional
,ld.total_unidades_privadas 
from {esquema}{punto}ilc_predio lp
left join {esquema}{punto}cr_datosphcondominio ld on ld.ilc_predio =lp.t_id
where substring(lp.numero_predial_nacional,22,9)='900000000' 
),
predios_asociados as (
select 
lp.numero_predial_nacional predio_matriz, 
lp.t_id tid_matriz, 
count(lpc.unidad_predial) conteo_unidades
from {esquema}{punto}ilc_predio lp
inner join tb_cond_1_30_1 tt on tt.t_id=lp.t_id
left join {esquema}{punto}cr_predio_copropiedad lpc on lpc.matriz =lp.t_id  
group by lp.t_id
),
tb_final as(
select 
tb1.numero_predial_nacional, 
tb1.total_unidades_privadas,
pa.conteo_unidades
from tb_cond_1_30_1 tb1
left join predios_asociados pa on tb1.t_id=pa.tid_matriz
),
tb_final_cond_1_30 as(
select 
numero_predial_nacional matriz, 
total_unidades_privadas,
conteo_unidades, 
case when total_unidades_privadas is null or conteo_unidades is null then 'Fail' 
	when total_unidades_privadas = conteo_unidades::int then 'OK' else 'Fail' end as cond_1_30 from tb_final)
select * from tb_final_cond_1_30
where cond_1_30 ='Fail'