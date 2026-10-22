with base as
(select 
lp.numero_predial
,ld.primer_nombre_reconocedor 
,ld.primer_apellido_reconocedor 
,case when ld.primer_nombre_reconocedor is null or ld.primer_apellido_reconocedor is null then 'Fail' else 'Ok' end as cond_1_59
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
)
select * from base
where cond_1_59 = 'Fail'
