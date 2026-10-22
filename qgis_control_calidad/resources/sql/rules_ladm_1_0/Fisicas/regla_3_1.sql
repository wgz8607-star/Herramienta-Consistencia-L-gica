with tb1 as(select 
lp.numero_predial
,lc.ilicode condicion_predio
,case when lu.t_id is null then 'Fail' else 'Ok' end as cond_3_1
from {esquema}.lc_predio lp 
left join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
left join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
left join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion
where 1=1
and lc.ilicode in ('PH.Unidad_Predial')
)
select * from tb1 where cond_3_1 ='Fail'

