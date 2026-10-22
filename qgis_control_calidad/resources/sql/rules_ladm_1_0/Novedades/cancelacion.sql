with validacion_cancelados as(
select'{esquema}' mun,--nombre el municipio
lp.t_id tid_predio,
lp.numero_predial npn_predio,
ld.observaciones,
/*ld.t_id tid_datos_adic,
 * le.t_id tid_novedad,
 * le.tipo_novedad,*/
le.numero_predial npn_novedad,letn.ilicode,
case when (substring(lp.numero_predial,18,1)='9' or substring(lp.numero_predial,18,1)in ('A','B','C','D','E')) then 'Fail'else 'OK' end as CONDICION_16,
case when substring(lp.numero_predial,22,1)='2' then 'Fail' else 'OK' end as CONDICION_17,
case when lp.numero_predial<>le.numero_predial then 'Fail' else 'OK' end as CONDICION_18,
case when ld.observaciones is null then 'Fail'
when ld.observaciones ilike '%cancela%' then 'OK' else 'Fail' end as CONDICION_19,
case when cu.t_id is not null then 'Fail' else 'OK' end as CONDICION_20
from {esquema}.lc_predio lp
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
inner join {esquema}.lc_estructuranovedadnumeropredial le  on le.lc_dtsdcnlstmntctstral_novedad_numeros_prediales =ld.t_id 
inner join {esquema}.lc_estructuranovedadnumeropredial_tipo_novedad letn on le.tipo_novedad =letn.t_id
left join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id 
where letn.ilicode= 'Cancelacion')select * from validacion_cancelados
where 1=1
and (CONDICION_16 ='Fail' or CONDICION_17='Fail'or CONDICION_18='Fail' or CONDICION_19='Fail' or CONDICION_20 = 'Fail')
