--regla 3.17
with regla_3_17 as(
select ruc.codigo
, regexp_replace( ruc.planta, '[^0-9]', '', 'g')::numeric planta
, 'r_unidad_ctm12' capa
from {esquema}{punto}r_unidad_ctm12 ruc 
union 
select rui.codigo
, regexp_replace( rui.planta, '[^0-9]', '', 'g')::numeric planta
, 'r_unidad_informal' capa
from {esquema}{punto}r_unidad_informal rui  
union
select uui.codigo
,  regexp_replace( uui.planta, '[^0-9]', '', 'g')::numeric planta
, 'u_unidad_informal' capa
from {esquema}{punto}u_unidad_informal uui
union 
select uuc2.codigo 
, regexp_replace(uuc2.planta, '[^0-9]', '', 'g')::numeric planta
, 'u_unidad_ctm12' capa
from {esquema}{punto}u_unidad_ctm12 uuc2 
)
select regla_3_17.*
, cp.coordinador
, cp.usuario as reconocedor
, 'Fail' cond_3_17
from regla_3_17
left join {esquema}{punto}cica_predio cp on regla_3_17.codigo = cp.numero_predial 
where planta <= 0
and cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')