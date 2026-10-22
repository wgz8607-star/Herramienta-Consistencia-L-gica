with base as(
select 
distinct
lp.numero_predial
,lc.t_id 
,lc.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad_construccion
,lu3.ilicode uso
,lc.total_plantas 
,case when lc.total_plantas is not null and lc.total_plantas >0  then 'Ok'
	else 'Fail' end as cond_3_24
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_construcciontipo lc2 on lc2.t_id =lc.tipo_construccion 
left join {esquema}{punto}lc_unidadconstrucciontipo lu2 on lu2.t_id =lc.tipo_unidad_construccion 
left join {esquema}{punto}lc_usouconstipo lu3 on lu3.t_id =lc.uso 
--where lu2.ilicode <> 'Comercial'
order by lp.numero_predial, lc.identificador 
)
select * from base
where cond_3_24 ='Fail'
