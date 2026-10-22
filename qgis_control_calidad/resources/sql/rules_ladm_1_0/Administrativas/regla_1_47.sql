with base as(select 
lp.numero_predial
,lc.ilicode clase_suelo
,etd.ilicode tipo_direccion
,case when etd.ilicode ='Estructurada' then 'Ok' else 'Fail' end as cond_1_47
from {esquema}.lc_predio lp 
LEFT JOIN {esquema}.lc_datosadicionaleslevantamientocatastral ldd ON ldd.lc_predio=lp.t_id
left join {esquema}.lc_clasesuelotipo lc on lc.t_id =ldd.clase_suelo 
left join {esquema}.extdireccion e on e.lc_predio_direccion =lp.t_id 
left join {esquema}.extdireccion_tipo_direccion etd on etd.t_id =e.tipo_direccion 
where lc.ilicode  ='Urbano'
)
select * from base where cond_1_47 ='Fail'
