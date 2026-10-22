with base as(
select 
li.t_id
,li2.ilicode tipo_interesado
,li3.ilicode documento_tipo
,li.documento_identidad 
,li.primer_nombre 
,li.segundo_nombre 
,li.primer_apellido 
,li.segundo_apellido
,ls.ilicode sexo
,case when ls.ilicode is not null then 'Fail' else 'Ok' end as cond_2_28
from {esquema}{punto}lc_interesado li 
left join {esquema}{punto}lc_interesadotipo li2 on li2.t_id =li.tipo 
left join {esquema}{punto}lc_interesadodocumentotipo li3 on li3.t_id =li.tipo_documento 
left join {esquema}{punto}lc_sexotipo ls on ls.t_id =li.sexo
where li2.ilicode <> 'Persona_Natural'
)
select * from base
where cond_2_28 ='Fail'