--cond 1.17
with tb_cond_1_17 as(
select 
lp.numero_predial
,lt.manzana_vereda_codigo 
,case when substring (lp.numero_predial,1,17)=lt.manzana_vereda_codigo then'OK' else 'Fail' end as cond_1_17
from {esquema}.lc_predio lp 
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id 
inner join {esquema}.lc_terreno lt on lt.t_id =cu.ue_lc_terreno
)
select * from tb_cond_1_15 where cond_1_17 ='Fail';
