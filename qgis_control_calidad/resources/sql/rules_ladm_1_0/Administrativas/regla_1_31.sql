--cond 1_31
with tb_cond_1_31_1 as (
select 
lp.t_id 
,lp.numero_predial
,ld.area_total_construida_privada
from {esquema}.lc_predio lp
left join {esquema}.lc_datosphcondominio ld on ld.lc_predio =lp.t_id
where substring(lp.numero_predial,22,9)='900000000' 
),
predios_asociados as (
select 
lp.numero_predial predio_matriz, 
lp.t_id tid_matriz, 
lpc.predio tid_unidad_predial
from {esquema}.lc_predio lp
inner join tb_cond_1_31_1 tt on tt.t_id=lp.t_id
left join {esquema}.lc_predio_copropiedad lpc on lpc.copropiedad =lp.t_id 
),
unidades_construccion as 
(
select 
distinct 
lp.t_id tid_unidad_predial,
lp.numero_predial, 
lu.identificador,
lu.area_construida,
lu.area_privada_construida 
from {esquema}.lc_predio lp
left join {esquema}.col_uebaunit cu on cu.baunit=lp.t_id and cu.ue_lc_unidadconstruccion is not null
left join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion
where lu.identificador is not null
),
predios_asociados_join_matriz as
(select 
pa.predio_matriz,
sum(uc.area_construida) unidades_prediales_area_construida_total,
sum(uc.area_privada_construida) unidades_prediales_area_privada_cosntruida_total
from predios_asociados pa
left join unidades_construccion uc on uc.tid_unidad_predial = pa.tid_unidad_predial
group by pa.predio_matriz
)
select 
tb1.numero_predial,
tb1.area_total_construida_privada,
pp.unidades_prediales_area_privada_cosntruida_total, 
case when tb1.area_total_construida_privada is null or pp.unidades_prediales_area_construida_total is null  then 'Fail'
when tb1.area_total_construida_privada = pp.unidades_prediales_area_privada_cosntruida_total then 'Ok' 
else 'Fail' end as cond_1_31
from tb_cond_1_31_1 tb1
inner join predios_asociados_join_matriz pp on pp.predio_matriz=tb1.numero_predial
;
