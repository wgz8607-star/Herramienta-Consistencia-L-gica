with base as(
select lp.numero_predial
,lo.numero_contacto_oferente 
,case when length(lo.numero_contacto_oferente)>10 or length(lo.numero_contacto_oferente)<7 then 'Fail'
	  when lo.numero_contacto_oferente  !~ '^[0-9]+$' then 'Fail' 
	  when lo.numero_contacto_oferente !~ '^(?!0+$)' then 'Fail'
	  else 'Ok' end as cond_4_28
from {esquema}.lc_predio lp 
inner join {esquema}.lc_ofertasmercadoinmobiliario lo on lo.lc_predio =lp.t_id 
)
select * from base
where cond_4_28='Fail'