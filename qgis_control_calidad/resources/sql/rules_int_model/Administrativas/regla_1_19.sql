--Regla 1.19 

with cancelados as (
select ip.numero_predial_nacional npn
, ietn.ilicode novedad
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on ip.t_id = id.ilc_predio 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ietn.ilicode in ('Cancelacion', 'Cancelacion_por_Desenglobe', 'Cancelacion_por_Englobe')
)
, tb_cond_1_19 as(
select ip.numero_predial_nacional
, ic.ilicode condicionpredio
, ct.t_ili_tid terreno_t_ili_tid
, ietn.ilicode novedad
, count (ct.t_id) over (partition by ip.numero_predial_nacional ) conteo
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id = ip.condicion_predio 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id and cu.ue_cr_terreno is not null
left join {esquema}{punto}cr_terreno ct on cu.ue_cr_terreno = ct.t_id 
left join cancelados c on c.npn = ip.numero_predial_nacional 
left join {esquema}{punto}ilc_datosadicionaleslevantamientocatastral id on ip.t_id = id.ilc_predio 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial ie on ie.ilc_dtsdcnltmntctstral_novedad_numeros_prediales = id.t_id 
left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ietn.t_id = ie.tipo_novedad 
where ic.ilicode in ('NPH','PH.Matriz','Condominio.Matriz','Condominio.Unidad_Predial','Via','Bien_Uso_Publico','Parque_Cementerio.Matriz', 'Informal')
and ip.numero_predial_nacional not in (coalesce(c.npn,'NO'))
and ct.t_id is null
union
select null
, null condicionpredio
, ct.t_ili_tid terreno_t_ili_tid
, null novedad
, count(ip.numero_predial_nacional) over (partition by ct.t_id) conteo
from {esquema}{punto}cr_terreno ct 
left join {esquema}{punto}col_uebaunit cu on cu.ue_cr_terreno = ct.t_id
left join {esquema}{punto}ilc_predio ip on ip.t_id = cu.baunit
)
select numero_predial_nacional
, terreno_t_ili_tid
, condicionpredio
, novedad
, conteo conteo_predioterreno
, 'Fail' cond_1_19 
from tb_cond_1_19 
where conteo <> 1
order by numero_predial_nacional, terreno_t_ili_tid
