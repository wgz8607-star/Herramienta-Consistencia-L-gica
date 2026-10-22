with base as(
select 
li.t_id
,li2.ilicode tipo_interesado
,li3.ilicode documento_tipo
,li.documento_identidad 
,case when li.documento_identidad ~ '^\d+(?:-\d)?$'  then 'Ok' 
		else 'Fail' end as cond_2_23
from {esquema}{punto}lc_interesado li 
left join {esquema}{punto}lc_interesadotipo li2 on li2.t_id =li.tipo 
left join {esquema}{punto}lc_interesadodocumentotipo li3 on li3.t_id =li.tipo_documento 
where li3.ilicode in ('NIT')
)
select * from base
where cond_2_23 ='Fail'