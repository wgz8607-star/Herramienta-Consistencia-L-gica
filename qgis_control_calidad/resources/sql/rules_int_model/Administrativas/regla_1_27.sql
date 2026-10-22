--regla 1.27
with tb_cond_1_27_1 as (
select 
lp.t_id 
,lp.numero_predial_nacional
,ld.area_total_construida_privada
from {esquema}{punto}ilc_predio lp
left join {esquema}{punto}cr_datosphcondominio ld on ld.ilc_predio =lp.t_id
where substring(lp.numero_predial_nacional,22,9)='900000000' 
),
predios_asociados as (
select 
lp.numero_predial_nacional predio_matriz, 
lp.t_id tid_matriz, 
lpc.unidad_predial tid_unidad_predial
from {esquema}{punto}ilc_predio lp
inner join tb_cond_1_27_1 tt on tt.t_id=lp.t_id
left join {esquema}{punto}cr_predio_copropiedad lpc on lpc.matriz =lp.t_id 
),
unidades_construccion as 
(
select 
distinct 
lp.t_id tid_unidad_predial,
lp.numero_predial_nacional, 
lc.t_id,
lc.identificador,
lc.area_construida,
lc.area_privada_construida 
from {esquema}{punto}ilc_predio lp
left join {esquema}{punto}col_uebaunit cu on cu.baunit=lp.t_id and cu.ue_cr_unidadconstruccion is not null
left join {esquema}{punto}cr_unidadconstruccion lu on lu.t_id =cu.ue_cr_unidadconstruccion
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion lc on lc.t_id =lu.cr_caracteristicasunidadconstruccion
where lc.identificador is not null
),
predios_asociados_join_matriz as
(select 
pa.predio_matriz,
sum(uc.area_construida) unidades_prediales_area_construida_total,
sum(uc.area_privada_construida) unidades_prediales_area_privada_cosntruida_total
from predios_asociados pa
left join unidades_construccion uc on uc.tid_unidad_predial = pa.tid_unidad_predial
group by pa.predio_matriz
),
validacion as
(select 
tb1.numero_predial_nacional,
tb1.area_total_construida_privada,
pp.unidades_prediales_area_privada_cosntruida_total, 
case when tb1.area_total_construida_privada is null or pp.unidades_prediales_area_construida_total is null  then 'Fail'
when tb1.area_total_construida_privada = pp.unidades_prediales_area_privada_cosntruida_total then 'Ok' 
else 'Fail' end as cond_1_27
from tb_cond_1_27_1 tb1
inner join predios_asociados_join_matriz pp on pp.predio_matriz=tb1.numero_predial_nacional
)
select *
from validacion
where validacion.cond_1_27 = 'Fail'