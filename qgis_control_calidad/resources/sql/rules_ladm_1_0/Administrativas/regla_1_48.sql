with base as(
select 
lp.numero_predial
,e.t_id 
,etd.ilicode 
,e.letra_via_principal
,e.letra_via_generadora 
,case when (e.letra_via_principal ~ '^[a-zA-Z]+$' or e.letra_via_principal is null) and (e.letra_via_generadora ~ '^[a-zA-Z]+$' or e.letra_via_generadora is null) then 'Ok' else 'Fail' end as cond_1_48
from {esquema}.lc_predio lp 
LEFT JOIN {esquema}.lc_datosadicionaleslevantamientocatastral ldd ON ldd.lc_predio=lp.t_id
left join {esquema}.lc_clasesuelotipo lc on lc.t_id =ldd.clase_suelo 
left join {esquema}.extdireccion e on e.lc_predio_direccion =lp.t_id 
left join {esquema}.extdireccion_tipo_direccion etd on etd.t_id =e.tipo_direccion 
where etd.ilicode  ='Estructurada' 
and (e.letra_via_principal is not null or e.letra_via_generadora is not null)
)
select * from base where cond_1_48 ='Fail';
