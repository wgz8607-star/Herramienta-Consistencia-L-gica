select 
li.documento_identidad 
,li2.departamento 
,li2.municipio 
,'Fail' as cond_2_37
from {esquema}.lc_interesado li 
inner join {esquema}.lc_interesadocontacto li2 on li2.lc_interesado =li.t_id 
where li2.departamento is null or li2.municipio is null
