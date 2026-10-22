--regla 3.36

with pisos as (
select ucc.codigo
, ucc.identificador
, ucc.numero_pisos::numeric  
, 'u_construccion_ctm12' tabla
, 'Fail' cond_3_36
from {esquema}{punto}u_construccion_ctm12 ucc 
union 
select uci.codigo
, uci.identificador
, uci.numero_pisos::numeric  
, 'u_construccion_informal' tabla
, 'Fail' cond_3_36
from {esquema}{punto}u_construccion_informal uci  
union 
select rcc.codigo
, rcc.identificador
, rcc.numero_pisos::numeric  
, 'r_construccion_ctm12' tabla
, 'Fail' cond_3_36
from {esquema}{punto}r_construccion_ctm12 rcc  
union 
select rci.codigo
, rci.identificador
, rci.numero_pisos::numeric  
, 'r_construccion_informal' tabla
, 'Fail' cond_3_36
from {esquema}{punto}r_construccion_informal rci 
)
select distinct 
p.codigo
, p.identificador
, p.numero_pisos numero_pisos_capa_geo_const
, p.tabla capa
, cp.coordinador as coordinador
, cp.usuario as reconocedor
, 'Fail' cond_3_36
from pisos p
left join {esquema}{punto}cica_predio cp on cp.numero_predial = p.codigo
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
and coalesce(p.numero_pisos,0)<1
order by p.codigo, p.identificador