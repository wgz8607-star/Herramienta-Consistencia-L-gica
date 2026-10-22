with base as
(select 
lp.numero_predial
,ld.numero_documento_reconocedor 
,case 
     when ld.numero_documento_reconocedor ~ '^[0-9]+$' and length(ld.numero_documento_reconocedor)  > '3' then 'Ok'else 'Fail' end as cond_1_58
from {esquema}.lc_predio lp 
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
)
select * from base where cond_1_58 = 'Fail'
