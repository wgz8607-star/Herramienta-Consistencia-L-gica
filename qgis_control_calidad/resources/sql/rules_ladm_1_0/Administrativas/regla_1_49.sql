with base as
(select 
lp.numero_predial
,li.ilicode tipo_documento_quien_atendio
,case when li.ilicode ='NIT' then 'Fail' else 'Ok' end as cond_1_49
from {esquema}.lc_predio lp 
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
inner join {esquema}.lc_contactovisita lc on lc.lc_datos_adicionales =ld.t_id 
inner join {esquema}.lc_interesadodocumentotipo li on li.t_id =lc.tipo_documento_quien_atendio 
)
select * from base where cond_1_49 = 'Fail'
