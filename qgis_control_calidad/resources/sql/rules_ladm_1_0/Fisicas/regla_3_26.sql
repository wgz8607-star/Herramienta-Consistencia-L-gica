with base as(
select 
distinct
lp.numero_predial
,lu.t_id 
,lu.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad_construccion
,lu3.ilicode uso
,lu.area_construida  
,case when  lu.area_construida IS null and lu.area_privada_construida >0 and lu.area_privada_construida is not null then 'OK'
	else 'Fail' end as cond_3_26
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
LEFT JOIN {esquema}.lc_condicionprediotipo lcpt ON lcpt.t_id=lp.condicion_predio
left join {esquema}.lc_construcciontipo lc2 on lc2.t_id =lu.tipo_construccion 
left join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion 
left join {esquema}.lc_usouconstipo lu3 on lu3.t_id =lu.uso 
WHERE lcpt.ilicode IN ('PH.Unidad_Predial','Condominio.Unidad_Predial')
order by lp.numero_predial, lu.identificador 
)
select * from base
where cond_3_26 ='Fail'
