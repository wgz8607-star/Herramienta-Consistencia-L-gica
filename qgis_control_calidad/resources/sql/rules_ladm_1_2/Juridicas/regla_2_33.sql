with base as
(
select 
la.t_id tid_agrupacion
,la.nombre nombre_agrupacion
,lat.ilicode tipo_agrupacion
,li2.ilicode tipo_interesado
from {esquema}{punto}lc_agrupacioninteresados la 
left join {esquema}{punto}col_grupointeresadotipo lat on lat.t_id =la.tipo 
left join {esquema}{punto}col_miembros cm on cm.agrupacion =la.t_id 
left join {esquema}{punto}lc_interesado li on li.t_id =cm.interesado_lc_interesado 
left join {esquema}{punto}lc_interesadotipo li2 on li2.t_id =li.tipo 
),
tb1 as(
select distinct  
tid_agrupacion
,tipo_agrupacion
,tipo_interesado
from base
order by tid_agrupacion),
tb2 as(select 
*,
count(tipo_interesado) over (partition by tid_agrupacion) conteo
from tb1),
tb_cond_2_33 as(
select
*
,case when tipo_agrupacion='Grupo_Empresarial' then 'Ok' else 'Fail' end as cond_2_33
from tb2 t where conteo=1
and tipo_interesado='Persona_Juridica')
select * from tb_cond_2_33
where cond_2_33 ='Fail'
