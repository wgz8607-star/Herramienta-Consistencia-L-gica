with base as( --tabla base en la cual se alistan todas las novedades
select 
'{esquema}' mun,--nombre el municipio 
lp.t_id tid_predio, 
lp.numero_predial npn_predio,
lp.tiene_fmi,
lp.matricula_inmobiliaria, 
/*ld.t_id tid_datos_adic,
le.t_id tid_novedad,
le.tipo_novedad,*/
le.numero_predial npn_novedad,
letn.itfcode cod_novedad,
letn.ilicode novedad,
rdcr.numero_predial npn_r1,
rdcr_2.numero_predial npn_r1_2
from {esquema}.lc_predio lp 
full outer join {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
full outer join {esquema}.lc_estructuranovedadnumeropredial le  on le.lc_dtsdcnlstmntctstral_novedad_numeros_prediales =ld.t_id 
full outer join {esquema}.lc_estructuranovedadnumeropredial_tipo_novedad letn on le.tipo_novedad =letn.t_id
--consulta cruzada contra el registro 1 (R1) de insumo inicial para validar si existe el registro, corresponde a las siguientes dos lineas
left join {esquema_r1}.{tabla_r1}  rdcr on rdcr.numero_predial = le.numero_predial 
left join {esquema_r1}.{tabla_r1}  rdcr_2 on rdcr_2.numero_predial = lp.numero_predial)
, desenglobe as( --se aislan los predios que tengan asociada novedad de desenglobe
select * from base where novedad ='Desenglobe'),
tb_base_desenglobes as(--se filtra la tabla base para q solo traiga numeros prediales de lc_predio que esten asociados a un desenglobe, ya sea en lc_predio o en lc_estructuranovedadnumeropredial
select *  from base 
where 1=1
and (npn_predio in (select npn_predio from desenglobe) 
or npn_predio in (select npn_novedad from desenglobe))
order by npn_novedad, novedad),
novedades_distintas as( --tabla para contar cuantos tipos distintos de novedades tiene asociado cada grupo de desenglobe
select count(distinct cod_novedad) c_d_novedad, npn_novedad from tb_base_desenglobes group by npn_novedad
),
tabla_intermedia_desenglobes as( --tabla intermedia para contar cuantos registros hay por grupo de desenglobe
select tbd.*
,count(tbd.npn_novedad) over (partition by tbd.npn_novedad) c_npn_novedad
,nd.c_d_novedad
from tb_base_desenglobes tbd
left join novedades_distintas nd on nd.npn_novedad=tbd.npn_novedad 
),
supuesto_posible_tipo_desenglobe as( -- se supone el tipo de desenglobe si es venta parcial o divison material con base en la cantidad de registros por grupo de desenglobe y con cantidad de novedades asociadas
select 
*
,case
    when tid.c_npn_novedad   =1 then                        'Indeterminado'
    when tid.c_d_novedad     >2 then                        'Indeterminado'
    when tid.c_npn_novedad   >1 and tid.c_d_novedad=1 then  'Venta Parcial'
    when tid.c_npn_novedad   =2 and tid.c_d_novedad=2 then  'Indeterminado'
    when tid.c_npn_novedad   >2 and tid.c_d_novedad=2 
        and 3 in (select cod_novedad 
        from tabla_intermedia_desenglobes tid2 
        where tid2.npn_novedad=tid.npn_novedad)
                                                      then  'Division Material'
 end as posible_tipo_desenglobe
from tabla_intermedia_desenglobes tid
),
supuesta_div_material as --tabla intermedia que valida si la supuesta division material cumple con la CONDICIONicion de que un registro dentro del grupo de desenglobe tenga el mismo numero predial en lc_predio y lc_estructuranovedadnumeropredial y esta sociacion tenga novedad de cancelacion
(
select 
*,
case
    when std.posible_tipo_desenglobe ='Division Material' and cod_novedad=3 and std.npn_predio=std.npn_novedad then 'OK' else 'Fail'
end as validacion
from supuesto_posible_tipo_desenglobe std
where std.posible_tipo_desenglobe='Division Material'
),
supuesta_venta_parcial as --tabla intermedia que valida si en la supuesta venta parcial haya almenos un registro que tenga el mismo numero predial en la relacion entre lc_predio y lc_estructuranovedadnumeropredial  y esa asociacion tenga novedad de desenglobe
(
select 
*,
--validar que solo coincida uno
case
    when std.posible_tipo_desenglobe ='Venta Parcial' and cod_novedad=1 and std.npn_predio=std.npn_novedad then 'OK'
    Else 'Fail'
end as validacion
from supuesto_posible_tipo_desenglobe std
where std.posible_tipo_desenglobe='Venta Parcial'
),
validacion_posible_tipo_desenglobe as --tabla que valida que cada grupo de deseglobe cumpla con las CONDICIONiciones minimas
(
select 
*,
case
    when std.posible_tipo_desenglobe ='Indeterminado' then 'Fail'
    when std.posible_tipo_desenglobe ='Division Material' and 'OK' in (select validacion from supuesta_div_material sdm where std.npn_novedad=sdm.npn_novedad) then 'OK'
    when std.posible_tipo_desenglobe ='Venta Parcial' and 'OK'  in (select validacion from supuesta_venta_parcial svp where std.npn_novedad=svp.npn_novedad) then 'OK'
    when std.posible_tipo_desenglobe ='Venta Parcial' and 'OK' not in (select validacion from supuesta_venta_parcial svp where std.npn_novedad=svp.npn_novedad) then 'Fail' else 'Fail'
    end as CONDICION_posible_tipo_desenglobe
from supuesto_posible_tipo_desenglobe std
),
validacion_otros_criterios as(
select *, 
--validacion lc_predio.numero_predial tiene fmi
case when tiene_fmi = true and matricula_inmobiliaria is not null then 'OK' else 'Fail' end as CONDICION_1,
--Validación lc_estructuranovedadnumeropredial.numero_predial existe en R1 
case when npn_r1 is null then 'Fail' else 'OK' end as CONDICION_2,
--validacion lc_estructuranovedadnumeropredial.numero_predial no es informal --> posc 22 <>2
case when substring(npn_novedad,22,1)='2' then 'Fail' else 'OK' end as CONDICION_3_1,
--validacion lc_predio.numero_predial no es predio informal --> posc 22 <>2
case when substring(npn_predio ,22,1)='2' then 'Fail' else 'OK' end as CONDICION_3_2,
--validacion lc_estructuranovedadnumeropredial.numero_predial no es predio nuevo --> posc 18 <>9
case when substring(npn_novedad,18,1) in ('9','A','B','C','D','E') then 'Fail' else 'OK' end as CONDICION_4,
case when posible_tipo_desenglobe <> 'Venta Parcial' then 'N/A'
when posible_tipo_desenglobe ='Venta Parcial' and 'OK'  in (select validacion from supuesta_venta_parcial svp where npn_novedad=npn_novedad) then 'OK'
when posible_tipo_desenglobe ='Venta Parcial' and 'OK' not in (select validacion from supuesta_venta_parcial svp where npn_novedad=npn_novedad) then 'Fail' else 'Fail'
end as CONDICION_5,
--Validación cuando sea DM, el número predial taba LC_predio debe existir en R1
case when posible_tipo_desenglobe = 'Division Material' and cod_novedad = 3 and npn_r1_2 is not null then 'OK'
when posible_tipo_desenglobe <> 'Division Material' then 'N/A'
when posible_tipo_desenglobe = 'Division Material' and cod_novedad <> 3 then 'N/A' else 'Fail' end as CONDICION_6,
--Validación lc_predio.numero_predial no existe en R1 cuando sea division material a menos que este asociado a la novedad de cancelación.
case when posible_tipo_desenglobe <> 'Division Material' then 'N/A' 
when posible_tipo_desenglobe = 'Division Material' and cod_novedad = 3 and npn_r1_2 is not null then 'OK'
when posible_tipo_desenglobe = 'Division Material' and cod_novedad <> 3 and npn_r1_2 is null then 'OK' else 'Fail' end as CONDICION_7
from validacion_posible_tipo_desenglobe)
select * 
 from validacion_otros_criterios
where 1=1 
and (CONDICION_1 ='Fail' or CONDICION_2='Fail'or CONDICION_3_1='Fail' or CONDICION_3_2='Fail' or CONDICION_4='Fail' or CONDICION_posible_tipo_desenglobe <> 'OK' or CONDICION_5 ='Fail' or CONDICION_6 = 'Fail' or CONDICION_7 = 'Fail')
order by npn_novedad
