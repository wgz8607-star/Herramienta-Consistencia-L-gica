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
,case when li.primer_nombre is null and li.segundo_nombre is null and li.primer_apellido is null and li.segundo_apellido is null and razon_social is not null then 'OK' else 'Fail' end as cond_2_27
from {esquema}{punto}lc_interesado li 
left join {esquema}{punto}lc_interesadotipo li2 on li2.t_id =li.tipo 
left join {esquema}{punto}lc_interesadodocumentotipo li3 on li3.t_id =li.tipo_documento 
where li2.ilicode = 'Persona_Juridica'
)
select * from base
where cond_2_27 ='Fail'