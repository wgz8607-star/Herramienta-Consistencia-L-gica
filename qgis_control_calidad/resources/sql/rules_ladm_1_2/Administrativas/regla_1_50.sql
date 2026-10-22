with base as
(select 
lp.numero_predial
,lc.numero_documento_quien_atendio
,case when lc.numero_documento_quien_atendio  ~ '^[0-9]+$' then 'Ok' else 'Fail' end as cond_1_50
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
inner join {esquema}{punto}lc_contactovisita lc on lc.lc_datos_adicionales =ld.t_id 
)
select * from base where cond_1_50 = 'Fail'
