-- Regla 8.9: Para novedad Englobe_Mantiene_FMI: los predios fuente deben quedar cancelados (Cancelacion_por_Englobe) y el predio resultado debe existir en novedades con Englobe_Mantiene_FMI.
-- Falla cuando: la estructura de englobe es incompleta o el predio resultado no tiene novedad Englobe_Mantiene_FMI.
-- Nota: la validación de existencia en R1 se omite aquí porque se cubre en la Regla 8.7.
with base_englobe as(
SELECT re.numero_predial npn_r1 ,
ip.numero_predial_nacional,
ip.matricula_inmobiliaria ,
ie.numero_predial npn_novedad,
ietn.ilicode tiponovedad
from {esquema}{punto}ilc_predio ip
left  join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
left join {esquema_r1}.{tabla_r1} re on re.numero_predial = ie.numero_predial
where ietn.ilicode in ('Englobe_Mantiene_FMI','Cancelacion_por_Englobe')
)
,englobe_novedad_asociada as (
select
te1.npn_r1,
te1.numero_predial_nacional,
te1.npn_novedad npn_novedad_1,
te1.tiponovedad novedad_1,
te2.npn_novedad npn_novedad_2,
te2.tiponovedad novedad_2,
count(te1.numero_predial_nacional) over (partition by te1.numero_predial_nacional) conteo_grupo
from base_englobe te1 left join base_englobe te2 on te1.npn_novedad=te2.numero_predial_nacional
where te1.tiponovedad='Englobe_Mantiene_FMI'
order by te1.numero_predial_nacional
)
,tb_final as(
select *,
case when conteo_grupo<3 then 'Fail' else 'Ok' end as val_conteo,
case when englobe_novedad_asociada.novedad_2='Cancelacion_por_Englobe' and npn_novedad_1 =npn_novedad_2 then 'Ok'
	 when englobe_novedad_asociada.novedad_1= 'Englobe_Mantiene_FMI' and numero_predial_nacional =npn_novedad_1 and npn_novedad_1=npn_novedad_2 then 'Ok'
	 when englobe_novedad_asociada.novedad_2 = 'Englobe_Mantiene_FMI' and englobe_novedad_asociada.novedad_2=englobe_novedad_asociada.novedad_1 and (englobe_novedad_asociada.npn_novedad_1,englobe_novedad_asociada.novedad_1) in (select tb22.npn_novedad_1, tb22.novedad_1 from englobe_novedad_asociada tb22) then 'OK'
	 else 'Fail' end as val_cohe,
case when npn_r1 is null then 'Fail' else 'Ok' end as val_r1
from englobe_novedad_asociada
order by numero_predial_nacional, npn_novedad_1 )
-- CTE extra: predios CxE cuyo predio resultado (el que mantiene FMI) no tiene Englobe_Mantiene_FMI en novedades
,cxe_sin_emf_resultado as (
    select
        null::text as npn_r1
        ,ip.numero_predial_nacional
        ,ie.numero_predial as npn_novedad_1
        ,ietn.ilicode as novedad_1
        ,null::text as npn_novedad_2
        ,null::text as novedad_2
        ,null::bigint as conteo_grupo
        ,'Fail - predio resultado sin Englobe_Mantiene_FMI' as val_conteo
        ,'Fail' as val_cohe
        ,null::text as val_r1
    from {esquema}{punto}ilc_predio ip
    join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on id.ilc_predio = ip.t_id
    join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id
    join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad
    where ietn.ilicode = 'Cancelacion_por_Englobe'
    and not exists (
        select 1
        from {esquema}{punto}ilc_predio ip2
        join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id2 on id2.ilc_predio = ip2.t_id
        join {esquema}{punto}ilc_estructuranovedadnumeropredial ie2 on ie2.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id2.t_id
        join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn2 on ietn2.t_id = ie2.tipo_novedad
        where ip2.numero_predial_nacional = ie.numero_predial
        and ietn2.ilicode = 'Englobe_Mantiene_FMI'
    )
)
select *, 'Fail' cond_8_9
from tb_final
where 'Fail' in (val_conteo,val_cohe)

union all

select *, 'Fail' cond_8_9
from cxe_sin_emf_resultado
