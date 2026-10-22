with base as(
select 
lp.numero_predial
,ldd.fecha_visita_predial 
,lp.tiene_fmi 
,lp.matricula_inmobiliaria 
,ld2.ilicode derecho_tipo
--,ld.fecha_inicio_tenencia 
,lf.fecha_documento_fuente 
,cf.ilicode fuente_adm_tipo
,lf.numero_fuente 
,lf.ente_emisor 
,case when (lf.fecha_documento_fuente 	is null) then 'Fail'
	  when (cf.ilicode 					is null or cf.ilicode 					~ '^\s*$') then 'Fail'
	  when (lf.numero_fuente 			is null or lf.numero_fuente 			~ '^\s*$') then 'Fail'
	  when (lf.ente_emisor 				is null or lf.ente_emisor				~ '^\s*$') then 'Fail'
	  when lf.fecha_documento_fuente <=ldd.fecha_visita_predial then 'Ok' else 'Fail' end as cond_2_18
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ldd on ldd.lc_predio =lp.t_id 
left join {esquema}{punto}lc_derecho ld on ld.unidad =lp.t_id 
left join {esquema}{punto}lc_derechotipo ld2 on ld2.t_id =ld.tipo 
left join {esquema}{punto}col_rrrfuente cr on cr.rrr_lc_derecho =ld.t_id 
left join {esquema}{punto}lc_fuenteadministrativa lf on lf.t_id =cr.fuente_administrativa 
left join {esquema}{punto}col_fuenteadministrativatipo cf on cf.t_id =lf.tipo
where lp.tiene_fmi =true
)
select * from base
where cond_2_18 ='Fail'