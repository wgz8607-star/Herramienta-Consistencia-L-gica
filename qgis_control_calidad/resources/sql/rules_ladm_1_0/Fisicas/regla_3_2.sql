with base as(select 
lp.numero_predial
,lc.ilicode condicion_predio
,lu.t_id 
,lu.identificador 
,ld.ilicode dominiotipo
,case when ld.ilicode = 'Privado' then 'Fail' when ld.ilicode ='Comun' then 'Ok' else 'Fail' end as cond_3_2
from {esquema}.lc_predio lp 
left join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
left join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
left join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion
left join {esquema}.lc_dominioconstrucciontipo ld on ld.t_id =lu.tipo_dominio 
where 1=1
and lc.ilicode in ('PH.Matriz','Condominio.Matriz')
)
select * from base where cond_3_2='Fail'