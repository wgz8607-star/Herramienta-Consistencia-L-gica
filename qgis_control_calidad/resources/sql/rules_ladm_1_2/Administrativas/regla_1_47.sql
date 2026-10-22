with base as(select 
lp.numero_predial
,lc.ilicode clase_suelo
,etd.ilicode tipo_direccion
,case when etd.ilicode ='Estructurada' then 'Ok' else 'Fail' end as cond_1_47
from {esquema}{punto}lc_predio lp 
left join {esquema}{punto}lc_clasesuelotipo lc on lc.t_id =lp.clase_suelo 
left join {esquema}{punto}extdireccion e on e.lc_predio_direccion =lp.t_id 
left join {esquema}{punto}extdireccion_tipo_direccion etd on etd.t_id =e.tipo_direccion 
where lc.ilicode  ='Urbano'
)
select * from base where cond_1_47 ='Fail'
