
with validacion_predio_nuevo as(
select 
'{esquema}' mun,--nombre el municipio
lp.t_id tid_predio, 
lp.numero_predial npn_predio,
/*ld.t_id tid_datos_adic,
le.t_id tid_novedad,
le.tipo_novedad,*/
le.numero_predial npn_novedad,
letn.ilicode,
rdcr.numero_predial npn_r1, 
case when lp.numero_predial<>le.numero_predial then 'Fail' else 'OK' end as CONDICION_26,
case when (substring(lp.numero_predial,18,1)='9' or substring(lp.numero_predial,18,1) in ('A','B','C','D','E')) then 'OK'else 'Fail' end as CONDICION_27,
case when rdcr.numero_predial is not null then 'Fail' else 'OK' end as CONDICION_28,
case when substring(le.numero_predial,22,1)in ('5','6') then 'Fail'else 'OK' end as CONDICION_29
from {esquema}.lc_predio lp 
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
inner join {esquema}.lc_estructuranovedadnumeropredial le  on le.lc_dtsdcnlstmntctstral_novedad_numeros_prediales =ld.t_id 
inner join {esquema}.lc_estructuranovedadnumeropredial_tipo_novedad letn on le.tipo_novedad =letn.t_id
left join {esquema_r1}.{tabla_r1}  rdcr on lp.numero_predial = rdcr.numero_predial 
where letn.ilicode= 'Predio_Nuevo')
select * from validacion_predio_nuevo
where 1=1 
and (CONDICION_26 ='Fail' or CONDICION_27 ='Fail'or CONDICION_28 ='Fail' or CONDICION_29 ='Fail')
