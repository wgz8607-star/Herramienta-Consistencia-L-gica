with base as
(select 
lp.numero_predial
,lc.celular 
,case when 	lc.celular is not null 
	    and lc.celular  ~ '^[0-9]+$' 
	    and length(lc.celular)=10 
	  then 'Ok' else 'Fail' end as cond_1_52
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
inner join {esquema}{punto}lc_contactovisita lc on lc.lc_datos_adicionales =ld.t_id
WHERE lc.celular IS NOT null
)
select * from base where cond_1_52 = 'Fail'
