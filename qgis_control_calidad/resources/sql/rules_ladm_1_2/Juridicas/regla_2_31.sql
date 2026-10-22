--validacion suma participacion
--regla 2.26
select 
ip.numero_predial 
,sum (coalesce(cm.participacion,0)) sumparticipacion
,'Fail' cond_2_31
from {esquema}{punto}lc_predio ip 
left join {esquema}{punto}lc_derecho id on id.unidad = ip.t_id
left join {esquema}{punto}col_miembros cm on cm.agrupacion = id.interesado_lc_agrupacioninteresados 
group by ip.numero_predial
having sum (coalesce(cm.participacion,0))<>1 and sum (coalesce(cm.participacion,0))<>0 and sum (coalesce(cm.participacion,0)) is not null