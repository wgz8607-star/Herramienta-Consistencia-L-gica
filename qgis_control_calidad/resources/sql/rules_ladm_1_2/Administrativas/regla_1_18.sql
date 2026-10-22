--cond 1.18
with tb_cond_1_18 as 
(
select 
lp.numero_predial
,ld.ilicode 
,cu.ue_lc_construccion 
,cu.ue_lc_unidadconstruccion 
,case when cu.ue_lc_construccion is not null or 
           cu.ue_lc_unidadconstruccion is not null 
      then 'Fail' else 'OK' end as cond_1_18
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_destinacioneconomicatipo ld on ld.t_id =lp.destinacion_economica 
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id 
where ld.ilicode ='Lote_Urbanizado_No_Construido'
)
select distinct * from tb_cond_1_18 
where cond_1_18 ='Fail';
