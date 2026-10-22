with base as
(select 
lp.numero_predial
,lc.autoriza_notificaciones  
,case when  lc.autoriza_notificaciones  = false then 'OK'
	when lc.autoriza_notificaciones  = true and (lc.correo_electronico is not null or lc.celular is not null) then 'Ok' else 'Fail' end as cond_1_54
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
inner join {esquema}{punto}lc_contactovisita lc on lc.lc_datos_adicionales =ld.t_id 
)
select * from base 
where cond_1_54 = 'Fail'
