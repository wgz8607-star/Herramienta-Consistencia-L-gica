--regla 2.26
select 
ip.numero_predial 
,sum(numerador::numeric/denominador::numeric) suma_participacion
,'Fail' cond_2_31
from {esquema}{punto}lc_predio ip 
left join {esquema}{punto}lc_derecho id on id.unidad = ip.t_id
left join {esquema}{punto}col_miembros cm on cm.agrupacion = id.interesado_lc_agrupacioninteresados 
left join {esquema}{punto}fraccion f on f.col_miembros_participacion =cm.t_id 
group by ip.numero_predial
having sum(numerador::numeric/denominador::numeric)<>1 and sum(numerador::numeric/denominador::numeric)<>0 and sum(numerador::numeric/denominador::numeric) is not null