--Regla 3.18
select ip.numero_predial_nacional, 
ic2.ilicode condicion, 
ic.identificador unidad, 
ic.area_construida, 
ic.area_privada_construida, 
'Fail' cond_3_18
--, ic.t_id 
from {esquema}{punto}ilc_caracteristicasunidadconstruccion ic 
left join {esquema}{punto}cr_unidadconstruccion cu on ic.t_id = cu.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}col_uebaunit cu2 on cu.t_id = cu2.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_predio ip on ip.t_id = cu2.baunit 
left join {esquema}{punto}ilc_condicionprediotipo ic2 on ic2.t_id = ip.condicion_predio
where ic2.ilicode in ('PH.Unidad_Predial','Condominio.Unidad_Predial')
and (ic.area_construida<>0 or ic.area_privada_construida = 0 or ic.area_privada_construida is null)
group by ic.t_id, ip.numero_predial_nacional, ic2.ilicode