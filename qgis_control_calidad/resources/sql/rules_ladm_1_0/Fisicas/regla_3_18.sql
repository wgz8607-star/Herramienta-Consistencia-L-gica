with base as(
select 
distinct
lp.numero_predial
,lu.t_id 
,lu.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad_construccion
,lu3.ilicode uso
,lu.total_locales
,case when lu3.ilicode is null then 'Fail' 
	 when lu3.ilicode not in ('Comercial.Parqueaderos','Comercial.Parqueaderos_en_PH') and (lu.total_locales >0 and lu.total_locales is not null) then 'Ok'
	 else 'Fail' end as cond_3_18
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}.lc_construcciontipo lc2 on lc2.t_id =lu.tipo_construccion 
left join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion 
left join {esquema}.lc_usouconstipo lu3 on lu3.t_id =lu.uso 
where lu2.ilicode ='Comercial'
order by lp.numero_predial, lu.identificador 
)
select * from base
where cond_3_18 ='Fail'

