select distinct '{esquema}' municipio,--nombre el municipio
lp.numero_predial lc_predio,
r1.numero_predial registro_1, 
le.numero_predial npn_novedad,
letn.ilicode, 
case when lp.numero_predial is null and le.numero_predial is null then 'Fail' else 'Ok' end as CONDICION_30
from {esquema}.lc_predio lp 
full outer join {esquema_r1}.{tabla_r1} r1 on lp.numero_predial = r1.numero_predial
full outer join {esquema}.lc_estructuranovedadnumeropredial le on le.numero_predial = r1.numero_predial 
and le.tipo_novedad in (select letn2.t_id from {esquema}.lc_estructuranovedadnumeropredial_tipo_novedad letn2 where letn2.ilicode in ('Cancelacion','Cambio_Numero_Predial')) 
full outer join {esquema}.lc_estructuranovedadnumeropredial_tipo_novedad letn on le.tipo_novedad = letn.t_id 
where case when lp.numero_predial is null and le.numero_predial is null then 'Fail' else 'Ok' end='Fail'
and substring (r1.numero_predial,1,5)='13212' --poner codigo de municipio 
and substring (r1.numero_predial,6,2)='00' --si tiene su base sectorizada, poner zona catastral, caso contrario comentariar esta linea de codigo
order by letn.ilicode
