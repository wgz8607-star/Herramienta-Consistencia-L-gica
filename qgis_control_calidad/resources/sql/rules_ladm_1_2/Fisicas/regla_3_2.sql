with base as(select 
lp.numero_predial
,lc.ilicode condicion_predio
,lc2.t_id 
,lc2.identificador 
,ld.ilicode dominiotipo
,case when ld.ilicode = 'Privado' then 'Fail' when ld.ilicode ='Comun' then 'Ok' else 'Fail' end as cond_3_2
from {esquema}{punto}lc_predio lp 
left join {esquema}{punto}lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
left join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
left join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc2 on lc2.t_id =lu.lc_caracteristicasunidadconstruccion 
left join {esquema}{punto}lc_dominioconstrucciontipo ld on ld.t_id =lc2.tipo_dominio 
where 1=1
and lc.ilicode in ('PH.Matriz','Condominio.Matriz')
)
select * from base where cond_3_2='Fail'