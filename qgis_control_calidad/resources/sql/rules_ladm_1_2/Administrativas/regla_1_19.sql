--cond 1.19
with tb_cond_1_19 as 
(
select 
lp.numero_predial
,ld.ilicode 
,case when cu.ue_lc_construccion is not null or 
	       cu.ue_lc_unidadconstruccion is not null 
	  then 'OK' else 'Fail' end as cond_1_19
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_destinacioneconomicatipo ld on ld.t_id =lp.destinacion_economica 
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_terreno is null and cu.ue_lc_servidumbretransito is null
where ld.ilicode in ('Comercial'
,'Educativo'
,'Habitacional'
,'Industrial'
,'Institucional'
,'Salubridad'
))
select * from tb_cond_1_19 
where cond_1_19 ='Fail';
