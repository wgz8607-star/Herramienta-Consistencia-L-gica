---Regla 1.54
select * from (select distinct on (ip.t_id)
    --ip.t_id,
    ip.numero_predial_nacional,
    ir.ilicode as resultado_visita,
   -- ietn.ilicode as Novedad,
    ic.t_id registro_ilc_contactovisita,  
    case 
        when ic.t_id is not null then 'OK'
        else 'fail'
    end as regla_1_54
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on ip.t_id = id.ilc_predio 
left join {esquema}{punto}ilc_resultadovisitatipo ir on id.resultado_visita = ir.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on id.t_id = ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
left join {esquema}{punto}ilc_contactovisita ic on ic.ilc_datos_adicionales = id.t_id
where ir.ilicode = 'Exitoso'
and (ietn.ilicode not like 'Cance%'or ietn.ilicode is NULL)) as regla
where regla.regla_1_54 = 'fail';