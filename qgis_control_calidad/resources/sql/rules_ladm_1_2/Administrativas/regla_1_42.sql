--cond 1_42
with tb_cond_1_42_1 as(
select 
lp.t_id 
,lp.numero_predial
,ld.total_unidades_privadas
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_datosphcondominio ld on ld.lc_predio =lp.t_id
where substring(lp.numero_predial,22,9)='800000000'
)
,predios_asociados as (
select 
lp.numero_predial predio_matriz, 
tt.total_unidades_privadas,
count(lpc.t_id) conteo
from {esquema}{punto}lc_predio lp
inner join tb_cond_1_42_1 tt on tt.t_id=lp.t_id
left join {esquema}{punto}lc_predio_copropiedad lpc on lpc.matriz =lp.t_id 
group by lp.numero_predial ,tt.total_unidades_privadas
)
select *,'Fail' cond_1_42 from predios_asociados pa
where coalesce(pa.total_unidades_privadas,0)=conteo or conteo=0