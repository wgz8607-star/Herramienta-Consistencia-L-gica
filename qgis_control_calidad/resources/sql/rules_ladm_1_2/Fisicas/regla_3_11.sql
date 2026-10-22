with base as(
select 
distinct
lp.numero_predial
,lc.t_id 
,lc.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad_construccion
,case when lu2.ilicode is null then 'Fail' 
	 when lu2.ilicode in ('Anexo') and lc2.ilicode ='No_Convencional' then 'Ok' else 'Fail' end as cond_3_11
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_construcciontipo lc2 on lc2.t_id =lc.tipo_construccion 
left join {esquema}{punto}lc_unidadconstrucciontipo lu2 on lu2.t_id =lc.tipo_unidad_construccion 
where lc2.ilicode ='No_Convencional'
order by lp.numero_predial, lc.identificador 
)
select * from base
where cond_3_11 ='Fail'


