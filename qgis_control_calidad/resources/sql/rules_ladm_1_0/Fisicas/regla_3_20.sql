with base as(
select distinct
lp.numero_predial
,ld2.ilicode destinacion_economica 
,lu.identificador 
, split_part(lu2.ilicode, '.', 1) uso
,lu.area_construida 
from {esquema}{punto}lc_predio lp 
left join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
left join {esquema}{punto}lc_destinacioneconomicatipo ld2 on ld2.t_id =ld.destinacion_economica 
left join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
left join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_usouconstipo lu2 on lu2.t_id =lu.uso 
where ld2.ilicode ='Habitacional'
)
,tb1 as(
select 
numero_predial,
destinacion_economica,
uso,
sum(coalesce(area_construida,0)) area_construida_total_uso
from base
group by 1,2,3)
,tb_final as(
select 
numero_predial, 
uso,
area_construida_total_uso ,
case when (select area_construida_total_uso from tb1 tt where tt.numero_predial=t.numero_predial and tt.uso='Residencial')< t.area_construida_total_uso and uso<>'Residencial' then 'Fail' 
when 'Residencial' not in (select coalesce(tt1.uso,'') from tb1 tt1 where tt1.numero_predial=t.numero_predial) then 'Fail' else 'Ok' end as cond_3_20_1
from tb1 t
order by numero_predial )
select numero_predial,
'Habitacional' dest_eco,
uso,
area_construida_total_uso,
'Fail' cond_3_20
from tb_final 
where numero_predial in (select numero_predial from tb_final where cond_3_20_1 ='Fail')
order by numero_predial 