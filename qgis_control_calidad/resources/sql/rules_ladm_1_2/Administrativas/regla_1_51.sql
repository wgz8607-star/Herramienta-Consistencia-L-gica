with base as
(select 
lp.numero_predial
,lc.primer_nombre_quien_atendio 
,lc.primer_apellido_quien_atendio 
,case when lc.primer_nombre_quien_atendio is not null and lc.primer_apellido_quien_atendio is not null then 'Ok' else 'Fail' end as cond_1_51
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
inner join {esquema}{punto}lc_contactovisita lc on lc.lc_datos_adicionales =ld.t_id 
)
select * from base where cond_1_51 = 'Fail'
