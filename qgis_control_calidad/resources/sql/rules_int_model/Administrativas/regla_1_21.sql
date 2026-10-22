

--Regla 1.21 nueva definicion
with tb1 as(
select 
ip.numero_predial_nacional 
,cpc.area_coeficiente 
,ic.ilicode  condicion_predio
,sum(coalesce(cpc.area_coeficiente,0)) over (partition by cpc.matriz) suma_area_coeficientes
,ip2.numero_predial_nacional npn_matriz
,cd.area_total_terreno
from  {esquema}{punto}ilc_predio ip
left join {esquema}{punto}cr_predio_copropiedad cpc on ip.t_id =cpc.unidad_predial 
left join {esquema}{punto}ilc_predio ip2 on ip2.t_id=cpc.matriz 
left join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio
left join {esquema}{punto}cr_datosphcondominio cd on cd.ilc_predio = ip2.t_id
where ic.ilicode in ('PH.Unidad_Predial','Condominio.Unidad_Predial','Parque_Cementerio.Unidad_Predial')
)
select *,'Fail' cond_1_21 from tb1
where area_total_terreno<>suma_area_coeficientes or area_total_terreno is null

/*Definicion anterior
--Regla 1.21
with tb1 as(
select 
ip.numero_predial_nacional, 
cpc.area_coeficiente , 
ic.ilicode  condicion_predio,
sum(coalesce(cpc.area_coeficiente,0)) over (partition by cpc.matriz) suma_area_coeficientes, 
ip2.numero_predial_nacional npn_matriz,
ip2.area_catastral_terreno area_matriz
from  {esquema}{punto}ilc_predio ip
left join {esquema}{punto}cr_predio_copropiedad cpc on ip.t_id =cpc.unidad_predial 
left join {esquema}{punto}ilc_predio ip2 on ip2.t_id=cpc.matriz 
left join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio
where ic.ilicode in ('PH.Unidad_Predial','Condominio.Unidad_Predial','Parque_Cementerio.Unidad_Predial')
)
select *,'Fail' cond_1_21 from tb1
where area_matriz<>suma_area_coeficientes or area_matriz is null
*/