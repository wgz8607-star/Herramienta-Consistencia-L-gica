with base as(
select 
distinct
lp.numero_predial
,lu.t_id 
,lu.planta_ubicacion 
,case when lu.planta_ubicacion <=0 or lu.planta_ubicacion is null then 'Fail' else 'Ok' end as cond_3_17
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
)
select * from base
where cond_3_17 ='Fail'
