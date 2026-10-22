--cond 1_34
with tb_cond_1_34_1 as (
select 
lp.t_id 
,lp.numero_predial
,ld.total_unidades_privadas 
from {esquema}.lc_predio lp
left join {esquema}.lc_datosphcondominio ld on ld.lc_predio =lp.t_id
where substring(lp.numero_predial,22,9)='900000000' 
),
predios_asociados as (
select 
lp.numero_predial predio_matriz, 
lp.t_id tid_matriz, 
count(lpc.predio) conteo_unidades
from {esquema}.lc_predio lp
inner join tb_cond_1_34_1 tt on tt.t_id=lp.t_id
left join {esquema}.lc_predio_copropiedad lpc on lpc.copropiedad =lp.t_id  
group by lp.t_id
),
tb_final as(
select 
tb1.numero_predial, 
tb1.total_unidades_privadas,
pa.conteo_unidades
from tb_cond_1_34_1 tb1
left join predios_asociados pa on tb1.t_id=pa.tid_matriz
)
select 
numero_predial matriz, 
total_unidades_privadas,
conteo_unidades, 
case when total_unidades_privadas is null or conteo_unidades is null then 'Fail' 
	when total_unidades_privadas = conteo_unidades::int then 'OK' else 'Fail' end as cond_1_34 from tb_final;
