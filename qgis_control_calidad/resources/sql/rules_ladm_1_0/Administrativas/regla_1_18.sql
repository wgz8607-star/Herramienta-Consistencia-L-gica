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
from {esquema}.lc_predio lp 
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ldd on ldd.lc_predio=lp.t_id
inner join {esquema}.lc_destinacioneconomicatipo ld on ld.t_id =ldd.destinacion_economica 
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id 
where ld.ilicode ='Lote_Urbanizado_No_Construido'
)
select distinct * from tb_cond_1_18 
where cond_1_18 ='Fail';
