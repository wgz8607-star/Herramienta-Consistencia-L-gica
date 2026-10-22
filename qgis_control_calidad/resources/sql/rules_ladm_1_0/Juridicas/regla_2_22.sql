with base as(
select 
li.t_id
,li2.ilicode tipo_interesado
,li3.ilicode documento_tipo
,li.documento_identidad 
--,case 
,case when li.documento_identidad is not null and 
			li.documento_identidad ~ '^[0-9]+$' and 
			li.documento_identidad !~ '^0+$' and 
			li.documento_identidad !~ '\s' then 'Ok' 
		else 'Fail' end as cond_2_22
from {esquema}.lc_interesado li 
left join {esquema}.lc_interesadotipo li2 on li2.t_id =li.tipo 
left join {esquema}.lc_interesadodocumentotipo li3 on li3.t_id =li.tipo_documento 
where li3.ilicode in ('Cedula_Ciudadania','Cedula_Extranjeria','Tarjeta_Identidad','Registro_Civil')
)
select * from base
where cond_2_22 ='Fail'