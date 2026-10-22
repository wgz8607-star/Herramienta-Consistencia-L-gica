--Regla 4.5
select ip.numero_predial_nacional, cc2.ilicode tipocalificacion, 
case when (coalesce (cc.tamanio_banio,0)+ coalesce (cc.enchape_banio,0)+ coalesce (cc.mobiliario_banio,0)+ coalesce (cc.conservacion_banio,0))>0 then 'Baño Con calificacion - Fail' else 'Baño sin calificacion - Ok' end as califbanio,
case when (coalesce (cc.tamanio_cocina,0)+ coalesce (cc.enchape_cocina,0)+ coalesce (cc.mobiliario_cocina,0)+ coalesce (cc.conservacion_cocina,0))>0 then 'Cocina Con calificacion - Fail' else 'Cocina sin calificacion - Ok' end as califcocina,
cc.cerchas_complemento_industria,
'Fail' cond_4_5
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu ON cu.baunit = ip.t_id 
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu.ue_cr_unidadconstruccion = cu2.t_id 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu2.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id 
left join {esquema}{punto}cuc_calificacionconvencional cc on cc.t_id = ccu.cuc_clfccnndcnstrccion_cuc_calificacionconvencional
left join {esquema}{punto}cuc_murostipo cm on cm.t_id = cc.muros
left join {esquema}{punto}cuc_fachadatipo cf on cf.t_id = cc.fachada
left join {esquema}{punto}cuc_cubrimiento_murostipo ccm on ccm.t_id = cc.cubrimiento_muros
left join {esquema}{punto}cuc_pisotipo cp on cp.t_id = cc.piso
left join {esquema}{punto}cuc_calificartipo cc2 on cc.tipo_calificacion = cc2.t_id 
where cc2.ilicode ='Industrial'
and ((coalesce (cc.tamanio_banio,0)+ coalesce (cc.enchape_banio,0)+ coalesce (cc.mobiliario_banio,0)+ coalesce (cc.conservacion_banio,0)) >0
 	or (coalesce (cc.tamanio_cocina,0)+ coalesce (cc.enchape_cocina,0)+ coalesce (cc.mobiliario_cocina,0)+ coalesce (cc.conservacion_cocina,0)) >0
 	or cc.cerchas_complemento_industria is null
 	or cm.ilicode in (	'Materiales_Desecho_Esterilla')
 	or cf.ilicode in (	'Buena'
 						,'Lujosa'
 						)
 	or ccm.ilicode in (	'Marmol_Lujosos_Otros'
 						,'Madera_Piedra_Ornamental'
 						,'Estuco_Ceramica_Papel_Fino'
 						)
 	or cp.ilicode in (	'Retal_De_Marmol_Marmol_Otros_Lujosos'
 						,'Parquet_Alfombra_Retal_De_Marmol'
 						,'Tableta_Caucho_Acrilico_Granito_Baldosa_Fina'
 						,'Liston_Machihembrado'
 						)
 	)
 	