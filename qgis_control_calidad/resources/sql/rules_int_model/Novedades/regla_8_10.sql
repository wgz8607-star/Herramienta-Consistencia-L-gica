-- Regla 8.10: Los predios nuevos (pos18 provisional) deben tener asociada al menos una novedad que justifique su creación.
-- Falla cuando: un predio nuevo no tiene novedad de englobe, desenglobe o predio nuevo.
WITH predios_englobe_nuevo_fmi as(
SELECT 
ip.t_id tid_predio
,ip.numero_predial_nacional npn_predio
,ie.t_id tid_novedad
,ie.numero_predial npn_novedad
,ietn.ilicode tiponovedad
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode in ('Englobe_Nuevo_FMI','Cancelacion_por_Englobe')
order by npn_predio, tiponovedad, npn_novedad
)
,tb1_1 as (
select 
pn.tid_predio ,
pn.npn_predio, 
pn2.tid_predio,
pn.npn_novedad npn_novedad1, 
pn.tiponovedad tipo_novedad1, 
pn2.npn_predio npn_novedad_2, 
pn2.tiponovedad tipo_novedad_2,
case when row_number() over (partition by pn.tid_predio)=1 then 1 else 0 end as rn_1,
case when row_number() over (partition by pn.tid_predio,pn2.tid_predio order by pn2.tiponovedad)=1 and  pn2.tid_predio is not null then 1 else 0 end as rn_2
from predios_englobe_nuevo_fmi pn
left join predios_englobe_nuevo_fmi  pn2 on pn.npn_novedad=pn2.npn_predio
where pn.tiponovedad='Englobe_Nuevo_FMI'
order by npn_predio
)
,tb1 as(
select 
t.npn_predio
,t.npn_novedad1
,t.tipo_novedad1
,t.npn_novedad_2
,t.tipo_novedad_2
,sum(rn_1) over (partition by npn_predio) + sum(rn_2) over (partition by npn_predio) conteo_grupo
from tb1_1 t
)
,tb_validaciones as (
select 
r1.numero_predial npn_r1
,tb1.npn_predio
,tb1.npn_novedad1
,tb1.tipo_novedad1
,tb1.npn_novedad_2
,tb1.tipo_novedad_2
,tb1.conteo_grupo
,case when conteo_grupo>=4 then 'Ok' else 'Fail' end as val_conteo
,case when coalesce(tipo_novedad_2,'') = 'Cancelacion_por_Englobe' and coalesce(npn_novedad1,'')=coalesce(npn_novedad_2,'') then 'Ok' else 'Fail' end as val_cohe 
,case when r1.numero_predial is null then 'Fail' else 'Ok' end as val_r1
,case when substring(tb1.npn_predio,18,1)~ '^[A-Z9]$' then 'Ok' else 'Fail' end as val_npn_nuevo
from tb1
left join {esquema_r1}{punto}{tabla_r1} r1 on r1.numero_predial =tb1.npn_novedad1
order by npn_predio
)
,tb_cond_8_10 as(
select
tv.npn_r1
,tv.npn_predio
,tv.npn_novedad1
,tv.tipo_novedad1
,tv.npn_novedad_2
,tv.tipo_novedad_2
,tv.conteo_grupo
,tv.val_conteo
,tv.val_cohe
,tv.val_r1
,tv.val_npn_nuevo
, case when 'Fail' in (tv.val_conteo,tv.val_cohe,tv.val_npn_nuevo) then 'Fail' else 'Ok' end as cond_8_10
from tb_validaciones tv
)
select * from tb_cond_8_10 where npn_predio in(select npn_predio from tb_cond_8_10 where cond_8_10 ='Fail')

union all

-- Rama B: predios con Cancelacion_por_Englobe que no son referenciados por ningún Englobe_Nuevo_FMI/Englobe_Mantiene_FMI
select
null as npn_r1
,ip.numero_predial_nacional as npn_predio
,ie.numero_predial as npn_novedad1
,ietn.ilicode as tipo_novedad1
,null as npn_novedad_2
,null as tipo_novedad_2
,null as conteo_grupo
,null as val_conteo
,null as val_cohe
,null as val_r1
,null as val_npn_nuevo
,'Fail' as cond_8_10
from {esquema}{punto}ilc_predio ip
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
where ietn.ilicode = 'Cancelacion_por_Englobe'
  and not exists (
    -- existe algún predio con Englobe que referencie el NPN de este predio cancelado
    select 1
    from {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id2
    join {esquema}{punto}ilc_predio ip2 on ip2.t_id = id2.ilc_predio
    join {esquema}{punto}ilc_estructuranovedadnumeropredial ie2 on ie2.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id2.t_id
    join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn2 on ietn2.t_id = ie2.tipo_novedad
    where ietn2.ilicode in ('Englobe_Nuevo_FMI','Englobe_Mantiene_FMI')
    and ie2.numero_predial = ip.numero_predial_nacional
  )


