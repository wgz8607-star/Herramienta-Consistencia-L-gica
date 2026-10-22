with base as(
select 
distinct
lp.numero_predial
,lu.planta_ubicacion 
,lu.t_id tid_caract
,lc2.t_id tid_constr
,lu.identificador id_uc
,lc2.identificador id_c
,lu.anio_construccion 
,lu.total_pisos total_pisos_uc
,lc2.numero_pisos numero_pisos_c
,max(lu.planta_ubicacion) over (partition by lp.numero_predial, lu.identificador) max_plantas_uc
,max(lu.planta_ubicacion) over (partition by lp.numero_predial, lc2.identificador) max_plantas_c
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}.lc_construccion lc2 on lc2.t_id =lu.lc_construccion 
where 1=1
order by lp.numero_predial, lu.identificador 
),
tb_cond_3_31 as(
select * 
,case when max_plantas_c>numero_pisos_c then 'Fail'
      when max_plantas_uc > total_pisos_uc then 'Fail'
      when total_pisos_uc > numero_pisos_c then 'Fail'
      end as cond_3_31
from base
)
select 
distinct 
numero_predial, 
id_c identificador_construccion,
numero_pisos_c numero_pisos_construccion, 
total_pisos_uc total_pisos_unidad_cosntruccion,
max_plantas_c planta_mas_alta_unidades_cosntruccion_asociadas,
cond_3_31
from tb_cond_3_31
where cond_3_31 ='Fail'
