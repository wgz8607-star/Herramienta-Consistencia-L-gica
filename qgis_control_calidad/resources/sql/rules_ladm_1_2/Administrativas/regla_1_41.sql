select 
lp.t_id 
,lp.numero_predial
,ld.numero_torres
,'Fail' cond_1_41
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_datosphcondominio ld on ld.lc_predio =lp.t_id
where substring(lp.numero_predial,22,9)='800000000'
and (ld.numero_torres <> 0 or ld.numero_torres is null)