
with validacion_Cambio_Numero_Predial as(
select 
'{esquema}' mun,--nombre el municipio
lp.t_id tid_predio, 
lp.numero_predial npn_predio,
--substring(lp.numero_predial,22,1), 
le.numero_predial npn_novedad,
--substring(le.numero_predial,22,1), 
letn.ilicode,
rdcr.numero_predial, 
-- 
case when lp.numero_predial <>le.numero_predial then 'OK' else 'Fail' end as CONDICION_21_1,
case when le.numero_predial in (select lp2.numero_predial from {esquema}.lc_predio lp2) then 'Fail' else 'OK' end as CONDICION_21_2,
case when substring(le.numero_predial,18,1) in ('9','A','B','C','D','E') then 'Fail' else 'OK' end as CONDICION_22,
case when substring (le.numero_predial,22,1) = '2' then 'Fail' else 'OK' end as CONDICION_23, 
case when rdcr.numero_predial is null then 'OK' else 'Fail' end as CONDICION_24,
case when substring(lp.numero_predial,18,1) in ('9','A','B','C','D','E') then 'OK' else 'Fail' end as CONDICION_25
from  {esquema}.lc_predio lp
inner join  {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
inner join  {esquema}.lc_estructuranovedadnumeropredial le  on le.lc_dtsdcnlstmntctstral_novedad_numeros_prediales =ld.t_id 
inner join  {esquema}.lc_estructuranovedadnumeropredial_tipo_novedad letn on le.tipo_novedad =letn.t_id
left join {esquema_r1}.{tabla_r1}  rdcr on rdcr.numero_predial = lp.numero_predial 
where letn.ilicode= 'Cambio_Numero_Predial')
select * from validacion_Cambio_Numero_Predial
where 1=1 
and (CONDICION_21_1 ='Fail' or CONDICION_21_2='Fail'or CONDICION_22 = 'Fail' or CONDICION_23 = 'Fail' or CONDICION_24 = 'Fail' or CONDICION_25 = 'Fail')
