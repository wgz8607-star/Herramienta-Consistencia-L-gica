--regla 1.38
with tb_base as(
select ip.numero_predial_nacional npn_matriz,
cd.total_unidades_privadas,
count(distinct cpc.unidad_predial) conteo_up
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}cr_datosphcondominio cd on cd.ilc_predio = ip.t_id 
left join {esquema}{punto}cr_predio_copropiedad cpc on cpc.matriz =ip.t_id 
where substring(ip.numero_predial_nacional,22,9)='800000000' 
group by ip.numero_predial_nacional,cd.total_unidades_privadas
)
,tb_cond_1_38 as(
select t.*
, case when t.total_unidades_privadas=conteo_up then 'Ok' else 'Fail' end as cond_1_38
from tb_base t)
select * from tb_cond_1_38 where cond_1_38 ='Fail'