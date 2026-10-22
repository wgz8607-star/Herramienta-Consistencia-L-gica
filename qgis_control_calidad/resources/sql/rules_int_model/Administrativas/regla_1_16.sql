--Regla 1.16
with cancelados as(
select le.numero_predial, letn.ilicode from {esquema}{punto}.ilc_estructuranovedadnumeropredial le
inner join {esquema}{punto}.ilc_estructuranovedadnumeropredial_tipo_novedad letn on letn.t_id =le.tipo_novedad and letn.ilicode in ('Cancelacion','Cancelacion_por_Englobe','Cancelacion_por_Desenglobe')
),tb1 as(
select ip.numero_predial_nacional ,
substring (numero_predial_nacional,6,2) zona,
id.ilicode dest_eco,
cpp.ilicode condicion,
round(st_area(ct.geometria)::numeric,2) area_geom_terreno,
count(cu.ue_cr_unidadconstruccion) cant_unidades
from {esquema}{punto}.ilc_predio ip
left join {esquema}{punto}.ilc_destinacioneconomicatipo id on id.t_id =ip.destinacion_economica 
left join {esquema}{punto}.ilc_condicionprediotipo cpp on cpp.t_id=ip.condicion_predio
left join {esquema}{punto}.col_uebaunit cu on cu.baunit =ip.t_id and cu.ue_cr_unidadconstruccion is not null
left join {esquema}{punto}.col_uebaunit cu2 on cu2.baunit =ip.t_id and cu2.ue_cr_terreno is not null
left join {esquema}{punto}.cr_terreno ct on ct.t_id =cu2.ue_cr_terreno 
where id.ilicode in ('Lote_Rural')
group by 1,2,3,4,5)
,tb_cond_1_16 as(
select *, 
case when dest_eco = 'Lote_Rural' and (zona<>'00' or cant_unidades <> 0
or coalesce(area_geom_terreno,0) = 0
or coalesce(area_geom_terreno,0)>500
or condicion in ('PH.Matriz','PH.Unidad_Predial','Condominio.Matriz','Condominio.Unidad_Predial')) then 'Fail' 
	 else 'Ok' end as cond_1_16	 
from tb1)
select t.* from tb_cond_1_16 t
left join cancelados c on t.numero_predial_nacional=c.numero_predial
where cond_1_16 ='Fail'
and c.numero_predial is null