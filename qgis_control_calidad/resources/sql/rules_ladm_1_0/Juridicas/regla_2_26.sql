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
,case 	when li.primer_nombre ilike '%suc%' then 'Fail'
		when li.segundo_nombre ilike '%suc%' then 'Fail'
		when li.segundo_nombre !~ '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$' then 'Fail'
		end as cond_2_26
from {esquema}.lc_interesado li 
left join {esquema}.lc_interesadotipo li2 on li2.t_id =li.tipo 
left join {esquema}.lc_interesadodocumentotipo li3 on li3.t_id =li.tipo_documento 
where li2.ilicode = 'Persona_Natural'
)
select * from base
where cond_2_26 = 'Fail'