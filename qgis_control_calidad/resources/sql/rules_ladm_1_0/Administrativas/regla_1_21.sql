--Regla 1.21
with cancelados as(
select le.numero_predial, letn.ilicode from {esquema}{punto}lc_estructuranovedadnumeropredial le
inner join {esquema}{punto}lc_estructuranovedadnumeropredial_tipo_novedad letn on letn.t_id =le.tipo_novedad and letn.ilicode='Cancelacion'
),tb1 as(
select ip.numero_predial ,
substring (numero_predial,6,2) zona,
id.ilicode dest_eco,
cpp.ilicode condicion,
round(st_area(ct.geometria)::numeric,2) area_geom_terreno,
count(cu.ue_lc_unidadconstruccion) cant_unidades
from {esquema}{punto}lc_predio ip
left join {esquema}{punto}lc_datosadicionaleslevantamientocatastral ldd on ldd.lc_predio=ip.t_id
left join {esquema}{punto}lc_destinacioneconomicatipo id on id.t_id =ldd.destinacion_economica 
left join {esquema}{punto}lc_condicionprediotipo cpp on cpp.t_id=ip.condicion_predio
left join {esquema}{punto}col_uebaunit cu on cu.baunit =ip.t_id and cu.ue_lc_unidadconstruccion is not null
left join {esquema}{punto}col_uebaunit cu2 on cu2.baunit =ip.t_id and cu2.ue_lc_terreno is not null
left join {esquema}{punto}lc_terreno ct on ct.t_id =cu2.ue_lc_terreno 
where id.ilicode in ('Acuicola', 'Agricola', 'Agroindustrial', 'Agropecuario', 'Agroforestal', 'Forestal', 'Infraestructura_Asociada_Produccion_Agropecuaria', 'Infraestructura_Saneamiento_Basico', 'Mineria_Hidrocarburos', 'Pecuario' ,'Lote_Rural','Lote_Urbanizable_No_Urbanizado', 'Lote_Urbanizado_No_Construido')
group by 1,2,3,4,5
)
,tb_cond_1_21 as(
select *, 
case when dest_eco = 'Lote_Rural' and (zona<>'00' or cant_unidades <> 0 or coalesce(area_geom_terreno,0) =0 or coalesce(area_geom_terreno,0)>500 or condicion in ('PH.Matriz','PH.Unidad_Predial','Condominio.Matriz','Condominio.Unidad_Predial')) then 'Fail' 
	 when dest_eco in ('Lote_Urbanizable_No_Urbanizado', 'Lote_Urbanizado_No_Construido') and zona='00' then 'Fail' 
	 when dest_eco not in ('Lote_Urbanizable_No_Urbanizado', 'Lote_Urbanizado_No_Construido') and zona <>'00' then 'Fail'
	 else 'Ok' end as cond_1_21	 
from tb1)
select t.* from tb_cond_1_21 t 
left join cancelados c on t.numero_predial=c.numero_predial
where cond_1_21 ='Fail'
and c.numero_predial is null