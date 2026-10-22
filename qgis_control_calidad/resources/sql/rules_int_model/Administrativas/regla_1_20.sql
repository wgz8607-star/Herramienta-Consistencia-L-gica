with tb1 as(
select ip.numero_predial_nacional 
, case when cpc.t_id is null or cpc.coeficiente=0 then 'No'  else 'Si' end as diligenciamiento_ok
,sum(coalesce(coeficiente,0)) over (partition by cpc.matriz) suma
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id = ip.condicion_predio 
left join {esquema}{punto}cr_predio_copropiedad cpc on cpc.unidad_predial = ip.t_id 
where ic.ilicode in ('PH.Unidad_Predial', 'Condominio.Unidad_Predial')
)
select *,'Fail' cond_1_20 from tb1 where diligenciamiento_ok = 'No' or suma <>1