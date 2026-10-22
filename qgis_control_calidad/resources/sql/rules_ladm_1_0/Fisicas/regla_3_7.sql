with terrenos as(
select 
cu.ue_lc_terreno
,cu.baunit 
,count(*) over (partition by cu.ue_lc_terreno) conteo_terreno
from {esquema}.col_uebaunit cu
where cu.ue_lc_terreno is not null)
, terrenos_2 as(
select lp.numero_predial,'Terreno' tipo_ue ,terrenos.ue_lc_terreno tid_ue, 'Fail' cond_3_7 from terrenos 
inner join {esquema}.lc_predio lp on lp.t_id =terrenos.baunit
where conteo_terreno>1
),
construcciones as(
select 
cu.ue_lc_construccion
,cu.baunit 
,count(*) over (partition by cu.ue_lc_construccion) conteo_construcciones
from {esquema}.col_uebaunit cu
where cu.ue_lc_construccion  is not null
),
construcciones_2 as(
select lp.numero_predial,'Construccion' tipo_ue ,construcciones.ue_lc_construccion tid_ue, 'Fail' cond_3_7 from construcciones 
inner join {esquema}.lc_predio lp on lp.t_id =construcciones.baunit
where conteo_construcciones>1
),
unidades_construcciones as(
select 
cu.ue_lc_unidadconstruccion 
,cu.baunit 
,count(*) over (partition by cu.ue_lc_unidadconstruccion) conteo_unidades_construcciones
from {esquema}.col_uebaunit cu
where cu.ue_lc_unidadconstruccion  is not null
),
unidades_construcciones_2 as(
select lp.numero_predial,'Unidad Construccion' tipo_ue ,unidades_construcciones.ue_lc_unidadconstruccion tid_ue, 'Fail' cond_3_7 from unidades_construcciones 
inner join {esquema}.lc_predio lp on lp.t_id =unidades_construcciones.baunit
where conteo_unidades_construcciones>1
)
select * from unidades_construcciones_2
union all
select * from construcciones_2
union all
select * from terrenos_2
