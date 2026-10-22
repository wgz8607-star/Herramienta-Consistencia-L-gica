with base as(
select 
distinct
lp.numero_predial
,lu.t_id 
,lu.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad_construccion
,case when lu2.ilicode is null then 'Fail' 
	 when lu2.ilicode in ('Anexo') and lc2.ilicode ='No_Convencional' then 'Ok' else 'Fail' end as cond_3_11
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}.lc_construcciontipo lc2 on lc2.t_id =lu.tipo_construccion 
left join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion 
order by lp.numero_predial, lu.identificador 
where lc2.ilicode ='No_Convencional'
)
select * from base
where cond_3_11 ='Fail'


