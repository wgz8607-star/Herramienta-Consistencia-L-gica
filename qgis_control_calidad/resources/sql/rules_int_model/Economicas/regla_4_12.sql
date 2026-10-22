--regla 4.12
select ip.numero_predial_nacional,
ie.valor_comercial as valor_comercial_total, 
    round(ie.valor_comercial * 0.6, 2) as valor_comercial_60,
    to_char(
        ((ie.avaluo_catastral * 0.6) / round(ie.valor_comercial * 0.6, 4)*100),
        'FM999999990.00'
    ) as porcentaje,
ie.valor_comercial valor_comercial_total, 
ie.avaluo_catastral valor_catastral_total,
ie.valor_comercial_terreno, 
ie.avaluo_catastral_terreno valor_catastral_terreno, 
ie.valor_comercial_total_unidadesconstruccion,
ie.avaluo_catastral_total_unidadesconstruccion valor_catastral_construccion,
'Fail' cond_4_12
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_estructuraavaluo ie on ie.ilc_predio_avaluo = ip.t_id 
where ie.valor_comercial <= ie.avaluo_catastral  
or ie.valor_comercial_terreno <= ie.avaluo_catastral_terreno  
or (ie.valor_comercial_total_unidadesconstruccion <= ie.avaluo_catastral_total_unidadesconstruccion) and ie.valor_comercial_total_unidadesconstruccion <> 0
or round ((ie.avaluo_catastral * 0.6) / round(ie.valor_comercial  * 0.60, 2),2)*100 < 60
or ((ie.valor_comercial_total_unidadesconstruccion <= 0 and ie.avaluo_catastral_total_unidadesconstruccion > 0) or (ie.valor_comercial_total_unidadesconstruccion > 0 and ie.avaluo_catastral_total_unidadesconstruccion <= 0))