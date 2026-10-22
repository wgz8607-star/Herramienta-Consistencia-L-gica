with base as
(select 
lp.numero_predial
,li.ilicode tipo_doc_reco
,case when li.ilicode = 'NIT' then 'Fail' else 'Ok' end as cond_1_57
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
left join {esquema}{punto}lc_interesadodocumentotipo li on li.t_id =ld.tipo_documento_reconocedor 
)
select * from base where cond_1_57 = 'Fail'
