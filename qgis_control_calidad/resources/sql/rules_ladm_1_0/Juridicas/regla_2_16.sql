with base as(
select 
lp.numero_predial
,lp.tiene_fmi 
,lp.matricula_inmobiliaria 
,ld2.ilicode derecho_tipo
,ld.fecha_inicio_tenencia 
,lf.fecha_documento_fuente 
,case when ld.fecha_inicio_tenencia is null then 'Fail'
	when ld.fecha_inicio_tenencia is not null and ld.fecha_inicio_tenencia <lf.fecha_documento_fuente then 'Fail'
	when ld.fecha_inicio_tenencia is not null and ld.fecha_inicio_tenencia >=lf.fecha_documento_fuente then 'Ok'
	else 'Fail' end as cond_2_16
from {esquema}.lc_predio lp 
left join {esquema}.lc_derecho ld on ld.unidad =lp.t_id 
left join {esquema}.lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}.col_rrrfuente cr on cr.rrr_lc_derecho =ld.t_id 
left join {esquema}.lc_fuenteadministrativa lf on lf.t_id =cr.fuente_administrativa 
where lp.matricula_inmobiliaria is not null and lp.matricula_inmobiliaria <>'0'
and ld2.ilicode ='Dominio'
)
select * from base
where cond_2_16 ='Fail'