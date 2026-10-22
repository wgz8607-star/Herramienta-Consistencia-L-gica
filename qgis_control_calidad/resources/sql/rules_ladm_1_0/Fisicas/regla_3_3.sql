with base as(select 
lp.numero_predial
,lc.ilicode condicion_predio
,lu.t_id 
,lu.identificador 
,lu2.ilicode uso
,case when lu2.ilicode is null then 'Fail'
	 when lu2.ilicode like '%PH%' then 'OK'
	 else 'Fail' end as cond_3_3
from {esquema}.lc_predio lp 
left join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
left join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
left join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion
left join {esquema}.lc_usouconstipo lu2 on lu2.t_id = lu.uso 
where 1=1
and lc.ilicode in ('PH.Matriz','PH.Unidad_Predial','Condominio.Matriz','Condominio.Unidad_Predial')
)
select * from base 
where 1=1 
and cond_3_3='Fail'