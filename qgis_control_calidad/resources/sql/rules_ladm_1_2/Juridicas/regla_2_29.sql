select 
li.documento_identidad, 
li.primer_nombre,
li.segundo_nombre, 
li.primer_apellido, 
li.segundo_apellido, 
'Fail' as cond_2_29 
from {esquema}{punto}lc_interesado li 
left join {esquema}{punto}lc_interesadotipo li2 on li.tipo =li2.t_id 
where li2.ilicode ='Persona_Natural'
AND (
li.primer_nombre SIMILAR TO '%(LTDA|& CIA|S\. EN C|S\.C\.A|S\.A\.S)%'
or li.segundo_nombre SIMILAR TO '%(LTDA|& CIA|S\. EN C|S\.C\.A|S\.A\.S)%'
or li.primer_apellido SIMILAR TO '%(LTDA|& CIA|S\. EN C|S\.C\.A|S\.A\.S)%'
or li.segundo_apellido SIMILAR TO '%(LTDA|& CIA|S\. EN C|S\.C\.A|S\.A\.S)%'
)