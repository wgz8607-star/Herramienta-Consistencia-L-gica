with base as(
select 
distinct
lp.numero_predial
,lu.t_id 
,lu.altura  
,case when lu.altura <=0 or lu.altura is null then 'Fail' else 'Ok' end as cond_3_28
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
)
select * from base
where cond_3_28 ='Fail'
