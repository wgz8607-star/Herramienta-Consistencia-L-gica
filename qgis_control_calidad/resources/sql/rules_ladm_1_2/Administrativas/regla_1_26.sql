--cond 1_26
with tb_cond_1_26
as 
(
select 
lp.numero_predial
, CASE WHEN ld.t_id IS NULL THEN 'Fail' ELSE 'OK' END AS cond_1_26
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_datosphcondominio ld on ld.lc_predio =lp.t_id 
LEFT JOIN {esquema}{punto}lc_condicionprediotipo lc ON lp.condicion_predio=lc.t_id
WHERE 1=1 AND (substring(lp.numero_predial,22,9) in ('800000000','900000000') 
OR lc.ilicode IN ('PH.Matriz','Condominio.Matriz'))
)
select * from tb_cond_1_26
where cond_1_26 ='Fail';
