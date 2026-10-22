--regla 3.13


with tb1 as(
select ip.numero_predial_nacional,id.ilicode  dest_eco,coalesce(split_part(cu3.ilicode,'.',1),'') uso,
sum(st_area(cu2.geometria)::numeric) area_uc_id
, rank() over (partition by ip.numero_predial_nacional
,id.ilicode order by sum(st_area(cu2.geometria)::numeric) desc) rank_
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id and cu.ue_cr_unidadconstruccion is not null
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu2.t_id = cu.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic2 on ic2.t_id = cu2.cr_caracteristicasunidadconstruccion
left join {esquema}{punto}cr_usouconstipo cu3 on cu3.t_id = ic2.uso 
left join {esquema}{punto}ilc_destinacioneconomicatipo id on id.t_id =ip.destinacion_economica 
where id.ilicode in ('Residencial', 'Anexo')
group by ip.numero_predial_nacional,id.ilicode,split_part(cu3.ilicode,'.',1)
)
,tb_cond_3_13 as (
select *
,case when rank_=1 and uso not in ('Residencial', 'Anexo') then 'Fail' else 'Ok' end as cond_3_13
from tb1
order by numero_predial_nacional, area_uc_id desc
)
,tb_final as(
select numero_predial_nacional ,dest_eco, uso, round(area_uc_id,2) area, cond_3_13 , rank_
from tb_cond_3_13
where numero_predial_nacional in (select numero_predial_nacional from tb_cond_3_13 where cond_3_13='Fail')
order by numero_predial_nacional, area_uc_id
)
select numero_predial_nacional, dest_eco,string_agg(uso||': '||area,', ') uso_area, 'Fail' cond_3_13
from tb_final
group by numero_predial_nacional ,dest_eco