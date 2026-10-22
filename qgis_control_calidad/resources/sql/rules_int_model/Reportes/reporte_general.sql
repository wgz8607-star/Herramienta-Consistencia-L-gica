with tb1 as (
--fila 1
select 1 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode in ('NPH','Bien_Uso_Publico','Via','Parque_Cementerio.Matriz','Informal')
union all
--fila 2
(with tb1 as(select count(ip.numero_predial_nacional) count1 from {esquema}{punto}ilc_predio ip)
, tb2 as(select count(idc.numero_predial) count2 from {esquema}{punto}ilc_estructuranovedadnumeropredial idc)
select 2 id, count1+count2 Cantidad from tb1, tb2)
union all
--fila 3
select 3 id, count(ip.numero_predial_nacional) Cantidad from {esquema}{punto}ilc_predio ip
union all
--fila 4
select 4 id, count(ip.numero_predial_nacional) Cantidad from {esquema}{punto}ilc_predio ip
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode in ('PH.Matriz')
union all
--fila 5
select 5 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode in ('PH.Unidad_Predial')
union all
--fila 6
select 6 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode in ('Condominio.Matriz')
union all
--fila 7
select 7 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode in ('Condominio.Unidad_Predial')
union all
--fila 8
select 8 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip
where ip.matricula_inmobiliaria  is not null
union all
--fila 9
select 9 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip
where ip.matricula_inmobiliaria  is not null
union all
--fila 10
select 10 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_destinacioneconomicatipo ld on ld.t_id =ip.destinacion_economica  and ld.ilicode in ('Lote_Urbanizable_No_Urbanizado','Lote_Urbanizado_No_Construido','Lote_No_Urbanizable')
union all
--fila 11
select 11 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_destinacioneconomicatipo ld on ld.t_id =ip.destinacion_economica  and ld.ilicode in ('Lote_Rural')
union all
--fila 12
select 12 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_destinacioneconomicatipo ld on ld.t_id =ip.destinacion_economica  and ld.ilicode in ('Comercial', 'Educativo', 'Habitacional', 'Industrial', 'Institucional','Salubridad')
union all
--fila 13
select 13 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode not in ('PH.Unidad_Predial','Condominio.Unidad_Predial')
union all
--fila 14
select 14 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode in ('Condominio.Unidad_Predial', 'PH.Unidad_Predial')
union all
--fila 15
select 15 id, count(cpc.unidad_predial)
from {esquema}{punto}cr_predio_copropiedad cpc
union all
--fila 16
select 16 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode in ('PH.Matriz','Condominio.Matriz')
union all
--fila 17
select 17 id,count(ip.numero_predial_nacional) Cantidad
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode in ('Condominio.Unidad_Predial', 'PH.Unidad_Predial')
union all
--fila 18
select 18 id,count(e.t_id) Cantidad from {esquema}{punto}extdireccion e inner join {esquema}{punto}extdireccion_tipo_direccion etd on etd.t_id =e.tipo_direccion 
where etd.ilicode='Estructurada' 
union all
--fila 19
select 19 id,count(e.t_id) Cantidad from {esquema}{punto}extdireccion e inner join {esquema}{punto}extdireccion_tipo_direccion etd on etd.t_id =e.tipo_direccion 
where etd.ilicode='No_Estructurada' 
union all
--fila 20
select 20 id,count(ic.t_id) Cantidad from {esquema}{punto}ilc_contactovisita ic 
union all
--fila 21
select 21 id, count (ip.numero_predial_nacional) Cantidad from {esquema}{punto}ilc_predio ip left join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id = ip.condicion_predio 
where ilicode = 'Informal'
union all
--fila 22
select 22 id, count (t_id) Cantidad from {esquema}{punto}ilc_predio_informalidad
union all
--fila 23
select 23 id, count(t_id ) Cantidad from {esquema}{punto}ilc_tramitesderechosterritoriales it 
union all
--fila 24
select 24 id, count(ld.t_id) Cantidad from {esquema}{punto}ilc_derecho ld 
union all
--fila 25
select 25 id, count(ld.t_id) Cantidad from {esquema}{punto}ilc_derecho ld inner join {esquema}{punto}ilc_derechocatastraltipo ld2 on ld.tipo =ld2.t_id 
where ld2.ilicode ='Dominio'
union all
--fila 26
select 26 id, count(ld.t_id) cantidad from {esquema}{punto}ilc_derecho ld inner join {esquema}{punto}ilc_derechocatastraltipo ld2 on ld.tipo =ld2.t_id 
where ld2.ilicode ='Posesion'
union all
--fila 27
select 27 id, count(ip.t_id) cantidad from {esquema}{punto}ilc_predio ip inner join {esquema}{punto}ilc_prediotipo cu on cu.t_id =ip.tipo 
where cu.ilicode in ('Predio.Privado.Privado')
union all
--fila 28
select 28 id, count(ip.t_id) cantidad from {esquema}{punto}ilc_predio ip inner join {esquema}{punto}ilc_prediotipo cu on cu.t_id =ip.tipo 
where split_part( cu.ilicode, '.',2) ='Publico'
union all
--fila 29
select 29 id, count(ip.t_id) cantidad from {esquema}{punto}ilc_predio ip 
										inner join {esquema}{punto}ilc_derecho id on id.unidad = ip.t_id 
										inner join {esquema}{punto}ilc_derechocatastraltipo ld2 on id.tipo =ld2.t_id 
										inner join {esquema}{punto}ilc_prediotipo  cu on cu.t_id =ip.tipo 
where ld2.ilicode ='Dominio' and cu.ilicode in ('Predio.Publico.Baldio.Baldio','Predio.Publico.Baldio.Reserva_Indigena','Predio.Publico.Presunto_Baldio' )
union all
--fila 30
select 30 id, count(ip.t_id) cantidad from {esquema}{punto}ilc_predio ip inner join {esquema}{punto}ilc_prediotipo  cu on cu.t_id =ip.tipo 
where cu.ilicode ='Predio.Privado.Colectivo' 
union all
--fila 31
select 31 id, count(ip.t_id) cantidad from {esquema}{punto}ilc_predio ip 
										inner join {esquema}{punto}ilc_derecho id on id.unidad = ip.t_id 
										inner join {esquema}{punto}ilc_derechocatastraltipo ld2 on id.tipo =ld2.t_id 
										inner join {esquema}{punto}ilc_prediotipo  cu on cu.t_id =ip.tipo 
where ld2.ilicode ='Ocupacion' and cu.ilicode ='Predio.Publico.Presunto_Baldio'
union all
--fila 32
select 32 id, count(ip.t_id) cantidad from {esquema}{punto}ilc_predio ip 
										inner join {esquema}{punto}ilc_derecho id on id.unidad = ip.t_id 
										inner join {esquema}{punto}ilc_derechocatastraltipo ld2 on id.tipo =ld2.t_id 
										inner join {esquema}{punto}ilc_prediotipo  cu on cu.t_id =ip.tipo 
where ld2.ilicode ='Dominio' and cu.ilicode ='Predio.Publico.Fiscal_Patrimonial' 
union all
--fila 33
select 33 id, count (ip.t_id) cantidad from {esquema}{punto}ilc_predio ip left join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id = ip.condicion_predio 
where ic.ilicode in ('Bien_Uso_Publico', 'Via')
union all
--fila 34
select 34 id, count (ii.t_id) cantidad 
from {esquema}{punto}ilc_interesado ii 
left join {esquema}{punto}cr_interesadotipo ci on ii.tipo = ci.t_id
where ci.ilicode = 'Persona_Juridica'
union all
--fila 35
select 35 id, count (ii.t_id) cantidad 
from {esquema}{punto}ilc_interesado ii 
left join {esquema}{punto}cr_interesadotipo ci on ii.tipo = ci.t_id
where ci.ilicode = 'Persona_Natural'
union all
--fila 36
select 36 id, (with base as (
select ip.numero_predial_nacional npn, 
sum(case when ci.ilicode = 'Persona_Natural' then 1 else 0 end) as p_natural,
sum(case when ci.ilicode = 'Persona_Juridica' then 1 else 0 end) as p_juridica
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_derecho id on id.unidad = ip.t_id 
left JOIN {esquema}{punto}col_rrrinteresado cr on cr.rrr = id.t_id  
left join {esquema}{punto}cr_agrupacioninteresados ca on ca.t_id = cr.interesado_cr_agrupacioninteresados 
left join {esquema}{punto}col_miembros cm on cm.agrupacion = ca.t_id 
left join {esquema}{punto}ilc_interesado ii on ii.t_id = cm.interesado_ilc_interesado
left join {esquema}{punto}cr_interesadotipo ci on ii.tipo = ci.t_id
group by ip.numero_predial_nacional 
)
select count(*) from base
where p_natural > 0 and p_juridica > 0)
union all
--fila 37
select 37 id, (with base as (
select ip.numero_predial_nacional npn, 
sum(case when ci.ilicode = 'Persona_Natural' then 1 else 0 end) as p_natural,
sum(case when ci.ilicode = 'Persona_Juridica' then 1 else 0 end) as p_juridica
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_derecho id on id.unidad = ip.t_id 
left JOIN {esquema}{punto}col_rrrinteresado cr on cr.rrr = id.t_id  
left join {esquema}{punto}cr_agrupacioninteresados ca on ca.t_id = cr.interesado_cr_agrupacioninteresados 
left join {esquema}{punto}col_miembros cm on cm.agrupacion = ca.t_id 
left join {esquema}{punto}ilc_interesado ii on ii.t_id = cm.interesado_ilc_interesado
left join {esquema}{punto}cr_interesadotipo ci on ii.tipo = ci.t_id
group by ip.numero_predial_nacional 
)
select count(*) from base
where p_natural > 1 and p_juridica = 0)
union all
--fila 38
select 38 id, (with base as (
select ip.numero_predial_nacional npn, 
sum(case when ci.ilicode = 'Persona_Natural' then 1 else 0 end) as p_natural,
sum(case when ci.ilicode = 'Persona_Juridica' then 1 else 0 end) as p_juridica
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}ilc_derecho id on id.unidad = ip.t_id 
left JOIN {esquema}{punto}col_rrrinteresado cr on cr.rrr = id.t_id  
left join {esquema}{punto}cr_agrupacioninteresados ca on ca.t_id = cr.interesado_cr_agrupacioninteresados 
left join {esquema}{punto}col_miembros cm on cm.agrupacion = ca.t_id 
left join {esquema}{punto}ilc_interesado ii on ii.t_id = cm.interesado_ilc_interesado
left join {esquema}{punto}cr_interesadotipo ci on ii.tipo = ci.t_id
group by ip.numero_predial_nacional 
)
select count(*) from base
where p_natural = 0 and p_juridica > 1)
union all
--fila 39
select 39 id, count (t_id) cantidad from {esquema}{punto}col_miembros cm 
union all
--fila 40 
select 40 id, count (t_id) cantidad from {esquema}{punto}ilc_fuenteadministrativa
union all
--fila 41
select 41 id, count (t_id) cantidad from {esquema}{punto}ilc_interesado ii 
union all
--fila 42
select 42 id, count (ii.t_id)cantidad  from {esquema}{punto}ilc_interesado ii left join {esquema}{punto}ilc_autorreconocimientoetnicotipo ia on ii.grupo_etnico = ia.t_id
where ia.ilicode is not null and ia.ilicode <> 'Ninguno'
union all
--fila 43
select 43 id, count(ip.t_id) cantidad 
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode in ('PH.Matriz','Condominio.Matriz')
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =ip.t_id and cu.ue_cr_unidadconstruccion is not null
union all
--fila 44
select 44 id, count(ip.t_id) cantidad 
from {esquema}{punto}ilc_predio ip 
inner join {esquema}{punto}ilc_condicionprediotipo ic on ic.t_id =ip.condicion_predio and ic.ilicode not in ('PH.Matriz','Condominio.Matriz','PH.Unidad_Predial','Condominio.Unidad_Predial')
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =ip.t_id and cu.ue_cr_unidadconstruccion is not null
union all
--fila 45
(
with tb1 as (select count (t_id) count1 from {esquema}{punto}cr_unidadconstruccion cu)
	, tb2 as (select count(t_id) count2 from {esquema}{punto}cr_terreno ct)
select 45 id, count1 + count2 cantidad from tb1, tb2
)
union all
--fila 46
select 46 id, count(t_id) cantidad from {esquema}{punto}cr_terreno ct 
union all
--fila 47
select 47 id, count (t_id) cantidad from {esquema}{punto}cr_unidadconstruccion cu 
union all
--fila 48
select 48 id, count (cu.t_id) cantidad from {esquema}{punto}cr_unidadconstruccion cu 
								left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu.cr_caracteristicasunidadconstruccion
								left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
								where cu2.ilicode = 'Anexo'
union all
--fila 49
select 49 id, count (cu.t_id) cantidad from {esquema}{punto}cr_unidadconstruccion cu 
								left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu.cr_caracteristicasunidadconstruccion
								left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
								where cu2.ilicode = 'Comercial'
union all
--fila 50
select 50 id, count (cu.t_id) cantidad from {esquema}{punto}cr_unidadconstruccion cu 
								left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu.cr_caracteristicasunidadconstruccion
								left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
								where cu2.ilicode = 'Industrial'
union all
--fila 51
select 51 id, count (cu.t_id) cantidad from {esquema}{punto}cr_unidadconstruccion cu 
								left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu.cr_caracteristicasunidadconstruccion
								left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
								where cu2.ilicode = 'Institucional'
union all
--fila 52
select 52 id, count (cu.t_id) cantidad from {esquema}{punto}cr_unidadconstruccion cu 
								left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu.cr_caracteristicasunidadconstruccion
								left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
								where cu2.ilicode = 'Residencial'
union all
--fila 53
select 53 id, count (ip.t_id) cantidad from {esquema}{punto}ilc_predio ip left join {esquema}{punto}ilc_destinacioneconomicatipo id on id.t_id = ip.destinacion_economica
where id.ilicode = 'Habitacional'
union all
--fila 54
select 54 id, count (ip.t_id) cantidad from {esquema}{punto}ilc_predio ip left join {esquema}{punto}ilc_destinacioneconomicatipo id on id.t_id = ip.destinacion_economica
where id.ilicode = 'Comercial'
union all
--fila 55
select 55 id, count (ip.t_id) cantidad from {esquema}{punto}ilc_predio ip left join {esquema}{punto}ilc_destinacioneconomicatipo id on id.t_id = ip.destinacion_economica
where id.ilicode = 'Industrial'
union all
--fila 56
select 56 id, count (ip.t_id) cantidad from {esquema}{punto}ilc_predio ip left join {esquema}{punto}ilc_destinacioneconomicatipo id on id.t_id = ip.destinacion_economica
where id.ilicode in ('Institucional', 'Religioso', 'Educativo', 'Cultural')
union all
--fila 57
select 57 id, count (cu.t_id) from {esquema}{punto}cr_unidadconstruccion cu 
						left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on cu.cr_caracteristicasunidadconstruccion = ic.t_id
						left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
						left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id
where cu2.ilicode = 'Residencial' and ccu.cuc_clfccnndcnstrccion_cuc_tipologiaconstruccion is not null
union all
--fila 58
select 58 id, count (cu.t_id) from {esquema}{punto}cr_unidadconstruccion cu 
						left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on cu.cr_caracteristicasunidadconstruccion = ic.t_id
						left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
						left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id
where cu2.ilicode = 'Comercial' and ccu.cuc_clfccnndcnstrccion_cuc_tipologiaconstruccion is not null
union all
--fila 59
select 59 id, count (cu.t_id) from {esquema}{punto}cr_unidadconstruccion cu 
						left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on cu.cr_caracteristicasunidadconstruccion = ic.t_id
						left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
						left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id
where cu2.ilicode = 'Industrial' and ccu.cuc_clfccnndcnstrccion_cuc_tipologiaconstruccion is not null
union all
--fila 60
select 60 id, count (cu.t_id) from {esquema}{punto}cr_unidadconstruccion cu 
						left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on cu.cr_caracteristicasunidadconstruccion = ic.t_id
						left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
						left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id
where cu2.ilicode = 'Institucional' and ccu.cuc_clfccnndcnstrccion_cuc_tipologiaconstruccion is not null
union all
--fila 61
select 61 id, count (cu.t_id) from {esquema}{punto}cr_unidadconstruccion cu 
						left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on cu.cr_caracteristicasunidadconstruccion = ic.t_id
						left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
						left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id
where cu2.ilicode = 'Industrial' and ccu.cuc_clfccnndcnstrccion_cuc_calificacionconvencional is not null
union all
--fila 62
select 62 id, count (cu.t_id) from {esquema}{punto}cr_unidadconstruccion cu 
						left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on cu.cr_caracteristicasunidadconstruccion = ic.t_id
						left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = ic.tipo_unidad_construccion
						left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id
where cu2.ilicode = 'Residencial' and ccu.cuc_clfccnndcnstrccion_cuc_calificacionconvencional is not null
union all
--fila 63
select 63 id,  count (cu.t_id) from {esquema}{punto}cr_unidadconstruccion cu 
					left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu.cr_caracteristicasunidadconstruccion 
					left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id 
					left join {esquema}{punto}cuc_calificacionconvencional cc on cc.t_id = ccu.cuc_clfccnndcnstrccion_cuc_calificacionconvencional 
					left join {esquema}{punto}cuc_calificartipo cc2 on cc.tipo_calificacion = cc2.t_id 	
where cc2.ilicode ='Comercial' and ccu.cuc_clfccnndcnstrccion_cuc_calificacionconvencional is not null
union all
--fila 64
select 64 id, count (t_id) from {esquema}{punto}cuc_calificacionconvencional cc 
union all
--fila 65
select 65 id, count (t_id) from {esquema}{punto}ilc_estructuraavaluo ie 
union all
--fila 72
select 72 id, count (ie.t_id) from {esquema}{punto}ilc_estructuranovedadnumeropredial ie 
							left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ie.tipo_novedad = ietn.t_id 
							where split_part(ietn.ilicode, '_',1) = 'Desenglobe'
union all
--fila 73
select 73 id, count (ie.t_id) from {esquema}{punto}ilc_estructuranovedadnumeropredial ie 
							left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ie.tipo_novedad = ietn.t_id 
							where split_part(ietn.ilicode, '_',1) = 'Englobe'
union all
--fila 74
select 74 id, count (ie.t_id) from {esquema}{punto}ilc_estructuranovedadnumeropredial ie 
							left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ie.tipo_novedad = ietn.t_id 
							where ietn.ilicode like 'Cancelacion%'
union all
--fila 75
select 75 id, count (ie.t_id) from {esquema}{punto}ilc_estructuranovedadnumeropredial ie 
							left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ie.tipo_novedad = ietn.t_id 
							where ietn.ilicode like 'Cambio_Numero_Predial%'
union all
--fila 76
select 76 id, count (ie.t_id) from {esquema}{punto}ilc_estructuranovedadnumeropredial ie 
							left join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn on ie.tipo_novedad = ietn.t_id 
							where ietn.ilicode = 'Predio_Nuevo'
union all
--fila 77
select 77 id, count (numero_predial) from {esquema_r1}.{tabla_r1}
union all
--fila 78
select 78 id, count (t_id) cantidad from {esquema}{punto}ilc_estructuranovedadnumeropredial ie 						
),tb2 as(
select * from (values (1, 'Predios con condición NPH, Bien de uso público, Via, Parque cementerio e Informal', '1.1'),
(2, 'Sumatoria de todos los registros ilc_predio y lc_estructuranovedadnumeropredial', '1.2'),
(3, 'Total de predios', '1.3, 1.8-1.11, 1.39, 1.42, 2.29, 4.9'),
(4, 'Predios con condición PH matríz', '1.4, 1.25-1.30'),
(5, 'Predios con condición PH Unidad predial', '1.5, 3.1'),
(6, 'Predios con condición Condominio matríz', '1.6, 1.31-1.38'),
(7, 'Predios con condición Condominio Unidad predial', '1.7'),
(8, 'Predios con el campo tiene fmi en verdadero', '1.12'),
(9, 'Predios con el campo matricula_inmobiliaria diligenciado', '1.13,1.14, 1.18, 2.11, 2.12'),
(10, 'Predios con destionacion economica Lote_Urbanizable_No_Urbanizado, Lote_Urbanizado_No_Construido, Lote_No_Urbanizable', '1.15'),
(11, 'Predios con destionacion economica Lote_Rural', '1.16'),
(12, 'Predios con destinacion económica Comercial, Educativo , Habitacional, Industrial, Institucional y Salubridad', '1.17'),
(13, 'Predios con condicion NPH, PH matríz, Condominio matríz, Condominio Unidad predial, Vía,Bien de uso público y Parque cementerio matríz', '1.19, 3.19'),
(14, 'Predios con condición PH Unidad predial y Condominio Unidad predial', '1.20'),
(15, 'Todos los registros de CR_Predio_Copropiedad', '1.21'),
(16, 'Predios con condición PH matríz y Condominio matríz', '1.22'),
(17, 'Predios con condición PH Unidad predial y Condominio Unidad predial', '1.23, 1.24,1.49, 3.18'),
(18, 'Direcciones estructuradas', '1.40, 1.43'),
(19, 'Direcciones no estructuradas', '1.41'),
(20, 'Total de Contacto visita', '1.44-1.48'),
(21, 'Predios informales', '1.50'),
(22, 'Total registros de ilc_predio_informalidad', '1.51'),
(23, 'Total registros de ILC_TramitesDerechosTerritoriales', '1.52'),
(24, 'Total de derechos', '2.1'),
(25, 'Derechos en pleno dominio', '2.2'),
(26, 'Derechos en posesion', '2.3'),
(27, 'Predios tipo privado', '2.4'),
(28, 'Predios tipo públicos', '2.5'),
(29, 'Predios baldios con derecho de dominio', '2.6'),
(30, 'Predios tipo privado colectivo', '2.7'),
(31, 'Predios presunto baldio con derecho ocupación', '2.8'),
(32, 'Públicos fiscales patrimoniales y de uso público con derecho de dominio', '2.9'),
(33, 'Predios tipo Vía y de Uso Público', '2.10'),
(34, 'Interesados tipo Persona jurídica', '2.13, 2.16, 2.18, 2.20'),
(35, 'Interesados tipo Persona natural', '2.14, 2.15, 2.17, 2.19, 2.21, 2.22'),
(36, 'Total de Agrupación de interesados grupo mixto', '2.23'),
(37, 'Total de Agrupación de interesados grupo civil', '2.24'),
(38, 'Total de Agrupación de interesados grupo empresarial', '2.25'),
(39, 'Total de registros en COL_miembros', '2.26'),
(40, 'Total Fuentes administrativas', '2.27, 2.28'),
(41, 'Total de Interesados', '2.29 - 2.31'),
(42, 'Total de Interesados dentro d eun grupo etnico', '2.32'),
(43, 'Unidades de construcción asociadas a predios con condición PH matríz y Condominio matríz', '3.2'),
(44, 'Unidades de construcción asociadas a predios con condición diferente de PH matríz , PH Unidad predial, Condominio matríz y Condominio Unidad predial', '3.3'),
(45, 'Sumatoria de terrenos y unidades de construcción', '3.4'),
(46, 'Total de Terrenos', '3.5'),
(47, 'Total de registros en CR_UnidadConstruccion', '3.6, 3.12, 3.17, 3.20, 3.21'),
(48, 'Unidades de construccion tipo Anexo', '3.7'),
(49, 'Unidades de construccion tipo Comercial', '3.8'),
(50, 'Unidades de construccion tipo Industrial', '3.9'),
(51, 'Unidades de construccion tipo Institucional', '3.10'),
(52, 'Unidades de construccion tipo Residencial', '3.11'),
(53, 'Predios con destinación económica habitacional', '3.13'),
(54, 'Predios con destinación económica comercial', '3.14'),
(55, 'Predios con destinación económica industrial', '3.15'),
(56, 'Predios con destinación económica institucional', '3.16'),
(57, 'CR_UnidadConstruccion residenciales calificadas por tipologías', '4.1'),
(58, 'CR_UnidadConstruccion comerciales calificadas por tipologías', '4.2'),
(59, 'CR_UnidadConstruccion industriales calificadas por tipologías', '4.3'),
(60, 'CR_UnidadConstruccion institucionales calificadas por tipologías', '4.4'),
(61, 'CR_UnidadConstruccion industriales calificadas por método convencional', '4.5'),
(62, 'CR_UnidadConstruccion residenciales calificadas por método convencional', '4.6'),
(63, 'CR_UnidadConstruccion comerciales calificadas por método convencional', '4.7'),
(64, 'Todos los registros de CUC_CalificacionConvencional', '4.8'),
(65, 'Todos los registros de ILC_EstructuraAvaluo', '4.10 - 4.12'),
(72, 'Registros de ILC_EstructuraNovedadNumeroPredial con tipo de novedad desenglobe', '8.1 - 8.5'),
(73, 'Registros de ILC_EstructuraNovedadNumeroPredial con tipo de novedad englobe', '8.6 - 8.10'),
(74, 'Registros de ILC_EstructuraNovedadNumeroPredial con tipo de novedad cancelación', '8.11 - 8.14'),
(75, 'Registros de ILC_EstructuraNovedadNumeroPredial con tipo de novedad cambio de numero predial', '8.15 - 8.18'),
(76, 'Registros de ILC_EstructuraNovedadNumeroPredial con tipo de novedad predio nuevo', '8.19 - 8.22'),
(77, 'Todos los registros de R1', '8.23'),
(78, 'Todos los registros de ILC_EstructuraNovedadNumeroPredial', '8.24 - 8.27')
) q (id,descripcion,reglas_validacion_Afectadas))
select tb2.id, tb2.descripcion, tb1.cantidad, tb2.reglas_validacion_afectadas from tb1 inner join  tb2 on tb1.id=tb2.id
order by tb2.id asc
