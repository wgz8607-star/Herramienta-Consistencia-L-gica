with base as(
select 
li.t_id
,li2.ilicode tipo_interesado
,li3.ilicode documento_tipo
,li.documento_identidad 
,case when li3.ilicode not in ('Cedula_Ciudadania','Cedula_Extranjeria','Tarjeta_Identidad','Registro_Civil','Pasaporte','Secuencial') then 'Fail' else 'Ok' end as cond_2_21
from {esquema}{punto}lc_interesado li 
left join {esquema}{punto}lc_interesadotipo li2 on li2.t_id =li.tipo 
left join {esquema}{punto}lc_interesadodocumentotipo li3 on li3.t_id =li.tipo_documento 
where li2.ilicode ='Persona_Natural'
)
select * from base
where cond_2_21 ='Fail'