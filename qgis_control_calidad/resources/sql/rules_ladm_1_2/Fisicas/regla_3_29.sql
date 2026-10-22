with base as(
select 
distinct
lp.numero_predial
,lr.ilicode resultado_visita
,lc.t_id 
,lc.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad_construccion
,lu3.ilicode uso
,lc.total_habitaciones
,case when lu3.ilicode in ('Residencial.Apartamentos_4_y_mas_pisos_en_PH'
							,'Residencial.Apartamentos_Mas_De_4_Pisos'
							,'Residencial.Barracas'
							,'Residencial.Casa_Elbas'
							,'Residencial.Vivienda_Colonial'
							,'Residencial.Vivienda_Hasta_3_Pisos'
							,'Residencial.Vivienda_Hasta_3_Pisos_En_PH'
							,'Residencial.Vivienda_Recreacional'
							,'Residencial.Vivienda_Recreacional_En_PH') and lc.total_habitaciones >0 and lc.total_habitaciones is not null then 'Ok'
	when lu3.ilicode not in ('Residencial.Apartamentos_4_y_mas_pisos_en_PH'
							,'Residencial.Apartamentos_Mas_De_4_Pisos'
							,'Residencial.Barracas'
							,'Residencial.Casa_Elbas'
							,'Residencial.Vivienda_Colonial'
							,'Residencial.Vivienda_Hasta_3_Pisos'
							,'Residencial.Vivienda_Hasta_3_Pisos_En_PH'
							,'Residencial.Vivienda_Recreacional'
							,'Residencial.Vivienda_Recreacional_En_PH') and (lc.total_habitaciones is null or lc.total_habitaciones = 0) then 'Ok'
							else 'Fail' end as cond_3_29
from {esquema}{punto}lc_predio lp
left join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
left join {esquema}{punto}lc_resultadovisitatipo lr on lr.t_id =ld.resultado_visita 
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_construcciontipo lc2 on lc2.t_id =lc.tipo_construccion 
left join {esquema}{punto}lc_unidadconstrucciontipo lu2 on lu2.t_id =lc.tipo_unidad_construccion 
left join {esquema}{punto}lc_usouconstipo lu3 on lu3.t_id =lc.uso 
where 1=1
and lr.ilicode ='Exitoso' 
and lu2.ilicode = 'Residencial'
order by lp.numero_predial, lc.identificador 
)
select * from base
where cond_3_29 ='Fail'
