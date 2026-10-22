--regla 1.21
select 
cp.numero_predial 
,substring(cp.numero_predial,6,2) zona
,cp.clase_suelo 
,cp.destino
, cp.coordinador
, cp.usuario as reconocedor
,'Fail' cond_1_21
from {esquema}{punto}cica_predio cp 
left join (select numero_predial, count(*) cant_uc from {esquema}{punto}cica_unidad_construccion group by numero_predial) a on a.numero_predial= cp.numero_predial 
where cp.destino in ('U','L','N','M','Z','O','AA','AC','W','R','S','D','AD')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
and case when destino not in ('R','S') and substring(cp.numero_predial,6,2) <> '00' then 'Fail'
	 when destino in ('R','S') and substring(cp.numero_predial,6,2) ='00' then 'Fail' else 'Ok' end ='Fail'