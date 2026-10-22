--regla 4.8
with validacion_puntos (calificar_tipo, objetotipo, puntos) AS (
VALUES
('Residencial','Armazon.Madera',0),
('Residencial','Armazon.Prefabricado',1),
('Residencial','Armazon.Ladrillo_Bloque',2 ),
('Residencial','Armazon.Concreto_Hasta_Tres_Pisos',4 ),
('Residencial','Armazon.Concreto_Cuatro_O_Mas_Pisos',6 ),
('Residencial','Muros.Materiales_Desecho_Esterilla',0 ),
('Residencial','Muros.Bahareque_Adobe_Tapia',1 ),
('Residencial','Muros.Madera',2 ),
('Residencial','Muros.Concreto_Prefabricado',3 ),
('Residencial','Muros.Bloque_Ladrillo',4 ),
('Residencial','Cubierta.Materiales_Desecho_Telas_Asfalticas',1 ),
('Residencial','Cubierta.Zinc_Teja_De_Barro_Eternit_Rustico',3 ),
('Residencial','Cubierta.Entrepiso_Cubierta_Provisional_Prefabricado',6 ),
('Residencial','Cubierta.Eternit_O_Teja_De_Barro_Cubierta_Sencilla',9 ),
('Residencial','Cubierta.Azotea_Aluminio_Placa_Sencilla_Con_Eternit',13 ),
('Residencial','Cubierta.Placa_Impermeabilizada_Cubierta_Lujosa_U_Ornamenta',16),
('Residencial','Fachada.Pobre',0),
('Residencial','Fachada.Sencilla',2),
('Residencial','Fachada.Regular',4 ),
('Residencial','Fachada.Buena',6 ),
('Residencial','Fachada.Lujosa',8 ),
('Residencial','Cubrimiento_Muros.Sin_Cubrimiento',0 ),
('Residencial','Cubrimiento_Muros.Paniete_Papel_Comun_Ladrillo_Prensado',1 ),
('Residencial','Cubrimiento_Muros.Estuco_Ceramica_Papel_Fino',2 ),
('Residencial','Cubrimiento_Muros.Madera_Piedra_Ornamental',3 ),
('Residencial','Cubrimiento_Muros.Marmol_Lujosos_Otros',4 ),
('Residencial','Piso.Tierra_Pisada',0 ),
('Residencial','Piso.Cemento_Madera_Burda',2 ),
('Residencial','Piso.Baldosa_Comun_De_Cemento_Tablon_Ladrillo',3 ),
('Residencial','Piso.Liston_Machihembrado',4 ),
('Residencial','Piso.Tableta_Caucho_Acrilico_Granito_Baldosa_Fina',6 ),
('Residencial','Piso.Parquet_Alfombra_Retal_De_Marmol',8),
('Residencial','Piso.Retal_De_Marmol_Marmol_Otros_Lujosos',9),
('Residencial','Tamanio_Banio.Sin_Banio',0),
('Residencial','Tamanio_Banio.Pequenio',1),
('Residencial','Tamanio_Banio.Mediano',2 ),
('Residencial','Tamanio_Banio.Grande',3 ),
('Residencial','Enchape_Banio.Sin_Cubrimiento',0 ),
('Residencial','Enchape_Banio.Paniete_Baldosa_Comun_De_Cemento',1 ),
('Residencial','Enchape_Banio.Baldosin_Unicolor_Papel_Comun',2 ),
('Residencial','Enchape_Banio.Baldosin_Decorado_Papel_Fino',3 ),
('Residencial','Enchape_Banio.Ceramica_Cristanac_Granito',4 ),
('Residencial','Enchape_Banio.Marmol_Enchape_Lujoso',5 ),
('Residencial','Mobiliario_Banio.Pobre',0 ),
('Residencial','Mobiliario_Banio.Sencillo',3 ),
('Residencial','Mobiliario_Banio.Regular',6 ),
('Residencial','Mobiliario_Banio.Bueno',9 ),
('Residencial','Mobiliario_Banio.Lujoso',11),
('Residencial','Tamanio_Cocina.Sin_Cocina',0),
('Residencial','Tamanio_Cocina.Pequenia',1),
('Residencial','Tamanio_Cocina.Mediana',2 ),
('Residencial','Tamanio_Cocina.Grande',3 ),
('Residencial','Enchape_Cocina.Sin_Cubrimiento',0 ),
('Residencial','Enchape_Cocina.Paniete_Baldosa_De_Cemento',1 ),
('Residencial','Enchape_Cocina.Baldosin_Unicolor_Papel_Comun',2 ),
('Residencial','Enchape_Cocina.Baldosin_Decorado_Papel_Fino',3 ),
('Residencial','Enchape_Cocina.Ceramica_Cristanac_Granito',4 ),
('Residencial','Enchape_Cocina.Marmol_Enchape_Lujoso',5 ),
('Residencial','Mobiliario_Cocina.Pobre',0 ),
('Residencial','Mobiliario_Cocina.Sencillo',2 ),
('Residencial','Mobiliario_Cocina.Regular',3 ),
('Residencial','Mobiliario_Cocina.Bueno',4 ),
('Residencial','Mobiliario_Cocina.Lujoso',6),
('Comercial','Armazon.Madera',4 ),
('Comercial','Armazon.Prefabricado',8 ),
('Comercial','Armazon.Ladrillo_Bloque',12 ),
('Comercial','Armazon.Concreto_Hasta_Tres_Pisos',22),
('Comercial','Armazon.Concreto_Cuatro_O_Mas_Pisos',22),
('Comercial','Muros.Materiales_Desecho_Esterilla',0 ),
('Comercial','Muros.Bahareque_Adobe_Tapia',1 ),
('Comercial','Muros.Madera',2 ),
('Comercial','Muros.Concreto_Prefabricado',3),
('Comercial','Muros.Bloque_Ladrillo',4 ),
('Comercial','Cubierta.Materiales_Desecho_Telas_Asfalticas',1),
('Comercial','Cubierta.Zinc_Teja_De_Barro_Eternit_Rustico',3),
('Comercial','Cubierta.Entrepiso_Cubierta_Provisional_Prefabricado',6 ),
('Comercial','Cubierta.Eternit_O_Teja_De_Barro_Cubierta_Sencilla',9),
('Comercial','Cubierta.Azotea_Aluminio_Placa_Sencilla_Con_Eternit',13 ),
('Comercial','Cubierta.Placa_Impermeabilizada_Cubierta_Lujosa_U_Ornamenta',16),
('Comercial','Fachada.Pobre',2),
('Comercial','Fachada.Sencilla',4),
('Comercial','Fachada.Regular',6 ),
('Comercial','Fachada.Buena',8 ),
('Comercial','Fachada.Lujosa',12 ),
('Comercial','Cubrimiento_Muros.Sin_Cubrimiento',0 ),
('Comercial','Cubrimiento_Muros.Paniete_Papel_Comun_Ladrillo_Prensado',2 ),
('Comercial','Cubrimiento_Muros.Estuco_Ceramica_Papel_Fino',3 ),
('Comercial','Cubrimiento_Muros.Madera_Piedra_Ornamental',5 ),
('Comercial','Cubrimiento_Muros.Marmol_Lujosos_Otros',7 ),
('Comercial','Piso.Tierra_Pisada',0 ),
('Comercial','Piso.Cemento_Madera_Burda',3 ),
('Comercial','Piso.Baldosa_Comun_De_Cemento_Tablon_Ladrillo',5 ),
('Comercial','Piso.Liston_Machihembrado',7 ),
('Comercial','Piso.Tableta_Caucho_Acrilico_Granito_Baldosa_Fina',9 ),
('Comercial','Piso.Parquet_Alfombra_Retal_De_Marmol',11),
('Comercial','Piso.Retal_De_Marmol_Marmol_Otros_Lujosos',13),
('Comercial','Mobiliario_Banio.Pobre',0 ),
('Comercial','Mobiliario_Banio.Sencillo',3),
('Comercial','Mobiliario_Banio.Regular',6),
('Comercial','Mobiliario_Banio.Bueno',9 ),
('Comercial','Mobiliario_Banio.Lujoso',16),
('Comercial','Mobiliario_Cocina.Pobre',0),
('Comercial','Mobiliario_Cocina.Sencillo',3),
('Comercial','Mobiliario_Cocina.Regular',6),
('Comercial','Mobiliario_Cocina.Bueno',9),
('Comercial','Mobiliario_Cocina.Lujoso',13),
('Industrial','Armazon.Madera',4 ),
('Industrial','Armazon.Prefabricado',8 ),
('Industrial','Armazon.Ladrillo_Bloque',12 ),
('Industrial','Armazon.Concreto_Hasta_Tres_Pisos',22),
('Industrial','Armazon.Concreto_Cuatro_O_Mas_Pisos',22),
('Industrial','Muros.Bahareque_Adobe_Tapia',1 ),
('Industrial','Muros.Madera',2 ),
('Industrial','Muros.Concreto_Prefabricado',3),
('Industrial','Muros.Bloque_Ladrillo',4 ),
('Industrial','Cubierta.Materiales_Desecho_Telas_Asfalticas',1),
('Industrial','Cubierta.Zinc_Teja_De_Barro_Eternit_Rustico',3),
('Industrial','Cubierta.Entrepiso_Cubierta_Provisional_Prefabricado',6 ),
('Industrial','Cubierta.Eternit_O_Teja_De_Barro_Cubierta_Sencilla',9),
('Industrial','Cubierta.Azotea_Aluminio_Placa_Sencilla_Con_Eternit',13 ),
('Industrial','Cubierta.Placa_Impermeabilizada_Cubierta_Lujosa_U_Ornamenta',16),
('Industrial','Fachada.Pobre',2),
('Industrial','Fachada.Sencilla',4),
('Industrial','Fachada.Regular',6 ),
('Industrial','Cubrimiento_Muros.Sin_Cubrimiento',0 ),
('Industrial','Cubrimiento_Muros.Paniete_Papel_Comun_Ladrillo_Prensado',2  ),
('Industrial','Piso.Tierra_Pisada',0 ),
('Industrial','Piso.Cemento_Madera_Burda',3 ),
('Industrial','Piso.Baldosa_Comun_De_Cemento_Tablon_Ladrillo',5 ),
('Industrial','Cerchas_Complemento_Industria.Madera',6 ),
('Industrial','Cerchas_Complemento_Industria.Metalica_Liviana',12),
('Industrial','Cerchas_Complemento_Industria.Metalica_Mediana',22 ),
('Industrial','Cerchas_Complemento_Industria.Metalica_Pesada',34),
--('Industrial','Cerchas_Complemento_Industria.Altura',6),
('Residencial','Malo',0),
('Residencial','Regular',2),
('Residencial','Bueno',4),
('Residencial','Excelente',5),
('Comercial','Malo',0),
('Comercial','Regular',2),
('Comercial','Bueno',4),
('Comercial','Excelente',5),
('Industrial','Malo',0),
('Industrial','Regular',2),
('Industrial','Bueno',4),
('Industrial','Excelente',5)
),/*
conservacion_valores (conservacion,valor) as(
values
('Malo',0),
('Regular',2),
('Bueno',4),
('Excelente',5)
),*/tb1 as(
SELECT distinct
ip.numero_predial_nacional numero_predial_nacional, 
ic.identificador identificador,
cc2.ilicode tipocalificacion,
cc.total_calificacion total_calificacion,
'Armazon.'||ca2.ilicode armazontipo, 
'Muros.'||cm.ilicode murostipo,
'Cubierta.'||cc3.ilicode cubiertatipo,
ce.ilicode conservacion_estructura,
'Fachada.'||cf.ilicode fachada,
'Cubrimiento_Muros.'||ccm.ilicode cubrimiento_muros,
'Piso.'||cp.ilicode pisos,
ce2.ilicode conservacion_acabados,
'Tamanio_Banio.'||ctb.ilicode tamanio_banio,
'Enchape_Banio.'||ceb.ilicode enchape_banio,
'Mobiliario_Banio.'||cmb.ilicode mobiliario_banio,
ce3.ilicode conservacion_banio,
'Tamanio_Cocina.'||ctc.ilicode tamanio_cocina,
'Enchape_Cocina.'||cec.ilicode enchape_cocina,
'Mobiliario_Cocina.'||cmc.ilicode mobiliario_cocina,
ce4.ilicode conservacion_cocina,
'Cerchas_Complemento_Industria.'||cc4.ilicode cerchas,
'Fail' cond_4_8
FROM {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id 
left join {esquema}{punto}cr_unidadconstruccion cu2 on cu2.t_id = cu.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion ic on ic.t_id = cu2.cr_caracteristicasunidadconstruccion 
left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion = ic.t_id 
inner join {esquema}{punto}cuc_calificacionconvencional cc on cc.t_id = ccu.cuc_clfccnndcnstrccion_cuc_calificacionconvencional 
left join {esquema}{punto}cuc_calificartipo cc2 on cc2.t_id = cc.tipo_calificacion 
left join {esquema}{punto}cuc_armazontipo ca2 on cc.armazon = ca2.t_id
left join {esquema}{punto}cuc_murostipo cm on cm.t_id = cc.muros 
left join {esquema}{punto}cuc_cubiertatipo cc3 on cc3.t_id = cc.cubierta 
left join {esquema}{punto}cuc_estadoconservaciontipo ce on ce.t_id = cc.conservacion_estructura
left join {esquema}{punto}cuc_fachadatipo cf on cf.t_id = cc.fachada 
left join {esquema}{punto}cuc_cubrimiento_murostipo ccm on ccm.t_id = cc.cubrimiento_muros 
left join {esquema}{punto}cuc_pisotipo cp on cp.t_id = cc.piso 
left join {esquema}{punto}cuc_estadoconservaciontipo ce2 on ce2.t_id = cc.conservacion_acabados 
left join {esquema}{punto}cuc_tamanio_baniotipo ctb on ctb.t_id = cc.tamanio_banio 
left join {esquema}{punto}cuc_enchape_baniotipo ceb on ceb.t_id = cc.enchape_banio 
left join {esquema}{punto}cuc_mobiliario_baniotipo cmb on cmb.t_id = cc.mobiliario_banio 
left join {esquema}{punto}cuc_estadoconservaciontipo ce3 on ce3.t_id = cc.conservacion_banio 
left join {esquema}{punto}cuc_tamanio_cocinatipo ctc on ctc.t_id = cc.tamanio_cocina 
left join {esquema}{punto}cuc_enchape_cocinatipo cec on cec.t_id = cc.enchape_cocina 
left join {esquema}{punto}cuc_mobiliario_cocinatipo cmc on cmc.t_id = cc.mobiliario_cocina 
left join {esquema}{punto}cuc_estadoconservaciontipo ce4 on ce4.t_id = cc.conservacion_cocina 
left join {esquema}{punto}cuc_cerchascomplementoindustriatipo cc4 on cc4.t_id = cc.cerchas_complemento_industria 
),
cond_4_8 as (
select numero_predial_nacional, 
identificador,
tipocalificacion,
total_calificacion,
unnest(array['armazontipo'
,'murostipo'
,'cubiertatipo'
,'conservacion_estructura'
,'fachada'
,'cubrimiento_muros'
,'pisos'
,'conservacion_acabados'
,'tamanio_banio'
,'enchape_banio'
,'mobiliario_banio'
,'conservacion_banio'
,'tamanio_cocina'
,'enchape_cocina'
,'mobiliario_cocina'
,'conservacion_cocina']) col_name1,
unnest(array[armazontipo
,murostipo
,cubiertatipo
,conservacion_estructura
,fachada
,cubrimiento_muros
,pisos
,conservacion_acabados
,tamanio_banio
,enchape_banio
,mobiliario_banio
,conservacion_banio
,tamanio_cocina
,enchape_cocina
,mobiliario_cocina
,conservacion_cocina]) col_name2
from tb1
)
select numero_predial_nacional,
identificador,
total_calificacion,
sum(puntos) suma_puntos,
'Fail' cond_4_8
--,col_name1,
--col_name2,
--puntos
from cond_4_8
left join validacion_puntos vp on vp.calificar_tipo = identificador and vp.objetotipo = col_name2
group by numero_predial_nacional, identificador, total_calificacion
having sum(puntos) <> total_calificacion or sum(puntos)>=100 or total_calificacion>=100