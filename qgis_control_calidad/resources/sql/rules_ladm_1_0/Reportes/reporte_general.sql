with tb1 as (
select 1 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('NPH','Bien_Uso_Publico','Via','Parque_Cementerio.Matriz','Informal')
union all 
select 2 id, count(*) 
from {esquema}.lc_estructuranovedadnumeropredial le 
union all
select 3 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('PH.Matriz')
union all
select 4 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('PH.Unidad_Predial')
union all
select 5 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('Condominio.Matriz')
union all
select 6 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('Condominio.Unidad_Predial')
union all
select 7 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
union all
select 8 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp
where lp.tiene_fmi =true
union all
select 9 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp
where lp.matricula_inmobiliaria  is not null
union all
select 10 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ldd on ldd.lc_predio =lp.t_id
inner join {esquema}.lc_destinacioneconomicatipo ld on ld.t_id =ldd.destinacion_economica  and ld.ilicode in ('Lote_Urbanizado_No_Construido')
union all
select 11 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ldd on ldd.lc_predio =lp.t_id
inner join {esquema}.lc_destinacioneconomicatipo ld on ld.t_id =ldd.destinacion_economica  and ld.ilicode in ('Comercial','Educativo','Habitacional','Industrial','Institucional','Salubridad')
union all
select 12 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_datosadicionaleslevantamientocatastral ldd on ldd.lc_predio =lp.t_id
inner join {esquema}.lc_destinacioneconomicatipo ld on ld.t_id =ldd.destinacion_economica  and ld.ilicode in ('Lote_Urbanizado_No_Construido','Lote_Urbanizable_No_Urbanizado')
union all
select 13 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp
where lp.tiene_fmi =false
union all
select 14 id,count(ld.t_id) Cantidad from {esquema}.lc_datosadicionaleslevantamientocatastral ld 
where ld.tiene_area_registral =true
union all
select 15 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('NPH','PH.Matriz','Condominio.Matriz','Condominio.Unidad_Predial','Parque_Cementerio.Matriz','Via','Bien_Uso_Publico')
union all
select 16 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('PH.Unidad_Predial','Condominio.Unidad_Predial')
union all
select 17 id,count(lp.numero_predial) Cantidad
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('PH.Matriz','Condominio.Matriz')
union all
select 18 id,count(e.t_id) cantidad from {esquema}.extdireccion e inner join {esquema}.extdireccion_tipo_direccion etd on etd.t_id =e.tipo_direccion 
where etd.ilicode='Estructurada' 
union all
select 19 id,count(e.t_id) cantidad from {esquema}.extdireccion e inner join {esquema}.extdireccion_tipo_direccion etd on etd.t_id =e.tipo_direccion 
where etd.ilicode='No_Estructurada' 
union all
select 20 id,count(e.t_id) cantidad from {esquema}.extdireccion e
union all
select 21 id, count (*) cantidad
from {esquema}.lc_predio lp 
LEFT JOIN {esquema}.lc_datosadicionaleslevantamientocatastral ldd ON ldd.lc_predio=lp.t_id
left join {esquema}.lc_clasesuelotipo lc on lc.t_id =ldd.clase_suelo
where lc.ilicode = 'Urbano'
union all
select 22 id, count(t_id) cantidad from {esquema}.lc_contactovisita lc 
union all
select 23 id, count(t_id) cantidad from {esquema}.lc_datosadicionaleslevantamientocatastral ld 
union all
select 24 id, count(ld.t_id) cantidad from {esquema}.lc_derecho ld inner join {esquema}.lc_derechotipo ld2 on ld.tipo =ld2.t_id 
where ld2.ilicode ='Dominio'
union all
select 25 id, count(ld.t_id) cantidad from {esquema}.lc_derecho ld
union all
select 26 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp where substring(lp.numero_predial,22,1)<>'2' 
union all
select 27 id, count(ld.t_id) cantidad from {esquema}.lc_derecho ld inner join {esquema}.lc_derechotipo ld2 on ld.tipo =ld2.t_id 
where ld2.ilicode ='Posesion'
union all
select 28 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp inner join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
where cu.ilicode in ('Predio.Privado')
union all
select 29 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp inner join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
where cu.ilicode in ('Predio.Publico.Baldio','Predio.Publico.Fiscal','Predio.Publico.Patrimonial','Predio.Publico.Uso_Publico','Predio.Publico.Ejido')
union all
select 30 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp 
										inner join {esquema}.lc_derecho ld on ld.unidad =lp.t_id 
										inner join {esquema}.lc_derechotipo ld2 on ld.tipo =ld2.t_id 
										inner join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
where ld2.ilicode ='Dominio' and cu.ilicode ='Predio.Publico.Baldio'
union all
select 31 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp inner join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
where cu.ilicode in ('Predio.Territorio_Colectivo')
union all
select 32 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp 
										inner join {esquema}.lc_derecho ld on ld.unidad =lp.t_id 
										inner join {esquema}.lc_derechotipo ld2 on ld.tipo =ld2.t_id 
										inner join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
where ld2.ilicode ='Ocupacion' and cu.ilicode ='Predio.Publico.Baldio'
union all
select 33 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp 
										inner join {esquema}.lc_derecho ld on ld.unidad =lp.t_id 
										inner join {esquema}.lc_derechotipo ld2 on ld.tipo =ld2.t_id 
										inner join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
union all
select 34 id, count(lp.t_id) from {esquema}.lc_predio lp inner join {esquema}.lc_condicionprediotipo cu on cu.t_id =lp.condicion_predio  
where cu.ilicode in ('Via','Bien_Uso_Publico')	
union all
select 35 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp inner join {esquema}.col_unidadadministrativabasicatipo cu on cu.t_id =lp.tipo 
where cu.ilicode in ('Predio.Vacante')
union all
select 36 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp inner join {esquema}.lc_restriccion lr on lr.unidad  =lp.t_id 
union all
select 37 id, count(lp.t_id) cantidad from {esquema}.lc_predio lp where length(lp.matricula_inmobiliaria)>7
union all 
select 38 id, count(li.t_id) cantidad from {esquema}.lc_interesado li inner join {esquema}.lc_interesadotipo li2 on li2.t_id =li.tipo 
where li2.ilicode ='Persona_Juridica'
union all
select 39 id, count(li.t_id) cantidad from {esquema}.lc_interesado li inner join {esquema}.lc_interesadotipo li2 on li2.t_id =li.tipo 
where li2.ilicode ='Persona_Natural'
union all
select 40 id, count(li.t_id) cantidad from {esquema}.lc_interesado li
union all
select 41 id, count(la.t_id) cantidad from {esquema}.lc_agrupacioninteresados la inner join {esquema}.col_grupointeresadotipo cg on la.tipo = cg.t_id 
where cg.ilicode = 'Grupo_Mixto'
union all 
select 42 id, count(la.t_id) cantidad from {esquema}.lc_agrupacioninteresados la inner join {esquema}.col_grupointeresadotipo cg on la.tipo = cg.t_id 
where cg.ilicode = 'Grupo_Civil'
union all
select 43 id, count(la.t_id) cantidad from {esquema}.lc_agrupacioninteresados la inner join {esquema}.col_grupointeresadotipo cg on la.tipo = cg.t_id 
where cg.ilicode = 'Grupo_Empresarial'
union all 
select 44 id, count (*) from {esquema}.col_miembros cm 
union all
select 45 id, count(lf.t_id) cantidad from {esquema}.lc_fuenteadministrativa lf 
union all
select 46 id, count(li3.t_id) cantidad from {esquema}.lc_interesadocontacto li3 
union all
select 47 id, count(lp.t_id) 
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('PH.Matriz','Condominio.Matriz')
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
union all
select 48 id, count(lp.t_id) 
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('PH.Matriz','Condominio.Matriz','PH.Unidad_Predial','Condominio.Unidad_Predial')
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
union all
select 49 id, count(lp.t_id) 
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode not in ('PH.Matriz','Condominio.Matriz','PH.Unidad_Predial','Condominio.Unidad_Predial')
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
union all
select 50 id, count(cu.t_id) from {esquema}.col_uebaunit cu
union all
select 51 id, count(lt.t_id) from {esquema}.lc_terreno lt 
union all
select 52 id, count(lu.t_id) from {esquema}.lc_unidadconstruccion lu 
union all
select 53 id, count(lc.t_id) from {esquema}.lc_construccion lc   
union all
select 54 id, count(lu.t_id) from {esquema}.lc_unidadconstruccion lu 
inner join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion and lu2.ilicode <>'Anexo'
union all
select 55 id, count(lu.t_id) from {esquema}.lc_unidadconstruccion lu 
inner join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion and lu2.ilicode ='Anexo'
union all
select 56 id, count(lu.t_id) from {esquema}.lc_unidadconstruccion lu 
inner join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion and lu2.ilicode ='Comercial'
union all
select 57 id, count(lu.t_id) from {esquema}.lc_unidadconstruccion lu 
inner join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion and lu2.ilicode ='Industrial'
union all
select 58 id, count(lu.t_id) from {esquema}.lc_unidadconstruccion lu  
inner join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion and lu2.ilicode ='Institucional'
union all
select 59 id, count(lu.t_id) from {esquema}.lc_unidadconstruccion lu 
inner join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion and lu2.ilicode ='Residencial'
union all
select 60 id, count(lp.t_id) 
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode in ('PH.Unidad_Predial','Condominio.Unidad_Predial')
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
union all
select 61 id, count(lp.t_id) 
from {esquema}.lc_predio lp 
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio and lc.ilicode not in ('PH.Unidad_Predial','Condominio.Unidad_Predial')
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion is not null
union all
select 62 id, count(lu.t_id) from {esquema}.lc_unidadconstruccion lu  
inner join {esquema}.lc_construcciontipo lc3 on lc3.t_id =lu.tipo_construccion and lc3.ilicode = 'Convencional'
union all
select 63 id, count(lu.t_id) from {esquema}.lc_unidadconstruccion lu 
inner join {esquema}.lc_construcciontipo lc3 on lc3.t_id =lu.tipo_construccion and lc3.ilicode = 'No_Convencional'
union all
select 64 id, count(lg.t_id) from {esquema}.lc_grupocalificacion lg 
union all
select 65 id, count(lo.t_id) from {esquema}.lc_ofertasmercadoinmobiliario lo 
),tb2 as(
select * from (values (1,'Predios con condición NPH, Bien de uso público, Via, Parque cementerio e Informal','1.1'),
(2, 'Todos los registros lc_estructuranovedadnumeropredial', '1.2'),
(3,'Predios con condición PH matríz','1.4, 1.29-1.34'),
(4,'Predios con condición PH Unidad predial','1.5, 1.27, 1.28, 3.1'),
(5,'Predios con condición Condominio matríz','1.6,  1.35-1.42'),
(6,'Predios con condición Condominio Unidad predial','1.7'),
(7,'Total de predios','1.3, 1.8-1.11, 1.16-1.17, 1.20, 1.43, 1.47, 2.38'),
(8,'Predios con el campo tiene fmi en verdadero','1.12'),
(9,'Predios con el campo matricula_inmobiliaria diligenciado','1.13-1.15, 2.1, 2.16, 2.18'),
(10,'Predios con destionacion economica Lote urbanizado no construido','1.18'),
(11,'Predios con destinacion económica Comercial, Educativo , Habitacional, Industrial, Institucional y Salubridad','1.19'),
(12,'Predios con destionación económica Lote urbanizado no construido y Lote urbanizable no urbanizado','1.21'),
(13,'Predios sin fmi','1.22'),
(14,'Predios con área registral','1.23'),
(15,'Predios con condicion NPH, PH matríz, Condominio matríz, Condominio Unidad predial, Vía,Bien de uso público y Parque cementerio matríz','1.24'),
(16,'Predios con condición PH Unidad predial y Condominio Unidad predial','1.25, 1.60'),
(17,'Predios con condición PH matríz y Condominio matríz','1.26'),
(18,'Direcciones estructuradas','1.44'),
(19,'Direcciones no estructuradas','1.45'),
(20,'Total de direcciones','1.46, 1.48'),
(21,'Predios con clase de suelo Urbano','1.47'),
(22,'Total de Contacto visita','1.49-1.56'),
(23,'Total de Datos adcionales de levantamiento catastral','1.57-1.59'),
(24,'Derechos en pleno dominio','2.2'),
(25,'Total de derechos','2.3-2.4'),
(26,'Predios formales','2.5-2.6'),
(27,'Derechos en posesion','2.7'),
(28,'Predios tipo privado','2.8'),
(29,'Predios tipo públicos','2.9'),
(30,'Predios baldios con derecho de dominio','2.10'),
(31,'Predios tipo Territorio colectivo','2.11'),
(32,'Predios baldios con derecho ocupación','2.12'),
(33,'Públicos fiscales y patrimoniales con derecho de dominio','2.13'),
(34,'Predios con condición Vía y de Bien de uso Público','2.14'), 
(35,'Predios tipo Vacantes','2.15'),
(36,'Predios con Restricción','2.19'),
(37, 'Predios con folio en sistema antiguo (Matricula inmobiliaria mayor a 7 digitos)', '2.17'),
(38,'Interesados tipo Persona jurídica','2.20, 2.23, 2.27'),
(39,'Interesados tipo Persona natural','2.21-2.22, 2.24-2.25, 2.28-2.29'),
(40,'Total de Interesados','2.26, 2.36-2.37'),
(41, 'Total de Agrupación de interesados grupo mixto', '2.30'),
(42, 'Total de Agrupación de interesados grupo civil', '2.32'),
(43, 'Total de Agrupación de interesados grupo empresarial', '2.33'),
(44, 'Total de registros en COL_miembros', '2.31'),
(45,'Total Fuentes administrativas','2.34-2.36'),
(46,'Total Contacto interesado','2.37 - 2.40'),
(47,'Unidades de construcción asociadas a predios con condición PH matríz y Condominio matríz','3.2'),
(48,'Unidades de construcción asociadas a predios con condición PH matríz , PH Unidad predial, Condominio matríz y Condominio Unidad predial','3.3'),
(49,'Unidades de construcción asociadas a predios con condición diferente de PH matríz , PH Unidad predial, Condominio matríz y Condominio Unidad predial','3.4'),
(50,'Total de registros en col_uebaunit','3.5, 3.7'),
(51,'Total de Terrenos','3.6, 3.8'),
(52,'Total de Unidades de construcción','3.9, 3.17, 3.23, 3.24, 3.25, 3.28, 3.30-3.35, 3.38-3.39'),
(53, 'Total de Construcciones', '3.36-3.37'),
(54,'Unidades de construccion con tipo diferente de Anexo','3.10'),
(55,'Unidades de construccion tipo Anexo','3.11-3.12'),
(56,'Unidades de construccion tipo Comercial','3.13, 3.18-3.19, 3.21, 4.4, 4.13, 4.15, 4.17-4.18, 4.22-4.23'),
(57,'Unidades de construccion tipo Industrial','3.14, 3.22, 4.5, 4.14, 4.16, 4.19-4.20,  4.22-4.23'),
(58,'Unidades de construccion tipo Institucional','3.15, 4.6, 4.13, 4.15, 4.17-4.18,  4.22-4.23'),
(59,'Unidades de construccion tipo Residencial','3.16, 3.20, 3.29, 4.3, 4.9-4.12, 4.21'),
(60,'Unidades de construccion asociadas a predios tipo PH Unidad predial y Condominio Unidad predial','3.26'),
(61,'Unidades de construccion asociadas a predios tipo diferente de PH Unidad predial y Condominio Unidad predial','3.27'),
(62,'Unidades de construcción Convencional','4.1, 4.7-4.8'),
(63,'Unidades de construcción No convencional','4.2'),
(64,'Total de registros en Grupo calificacion','4.24-4.25'),
(65,'Total de registros en Oferta de mercado inmobiliario','4.26-4.28')
) q (id,descripcion,reglas_validacion_Afectadas))
select tb2.id, tb2.descripcion, tb1.cantidad, tb2.reglas_validacion_afectadas from tb1 inner join tb2 on tb1.id=tb2.id
order by tb2.id asc