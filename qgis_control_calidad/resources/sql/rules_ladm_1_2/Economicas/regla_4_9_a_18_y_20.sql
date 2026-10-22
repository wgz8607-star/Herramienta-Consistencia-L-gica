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
('Residencial','Cubierta.Placa_Impermeabilizada_Cubierta_Lujosa_Ornamental',16),
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
('Residencial','Piso.Parquet_Alfombra_Retal_Marmol_Grano_Pequeño',8),
('Residencial','Piso.Retal_Marmol_Otros_Lujosos',9),
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
('Comercial','Cubierta.Placa_Impermeabilizada_Cubierta_Lujosa_Ornamental',16),
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
('Comercial','Piso.Parquet_Alfombra_Retal_Marmol_Grano_Pequeño',11),
('Comercial','Piso.Retal_Marmol_Otros_Lujosos',13),
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
('Industrial','Cubierta.Placa_Impermeabilizada_Cubierta_Lujosa_Ornamental',16),
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
('Industrial','Cerchas_Complemento_Industria.Altura',6)),
base as(
select 
distinct
lp.numero_predial
,lc.t_ili_tid  
,lc.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad
--,la.ilicode tipo_anexo
,lc4.ilicode tipo_calificar
,lc3.total_calificacion 
,lc5.ilicode clase_calificacion
,le.ilicode conservacion
,lo2.ilicode tipo_objeto
,lo.puntos 
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_construcciontipo lc2 on lc2.t_id =lc.tipo_construccion 
left join {esquema}{punto}lc_unidadconstrucciontipo lu2 on lu2.t_id =lc.tipo_unidad_construccion 
left join {esquema}{punto}lc_usouconstipo lu3 on lu3.t_id =lc.uso 
left join {esquema}{punto}lc_calificacionconvencional lc3 on lc3.lc_unidad_construccion =lc.t_id 
left join {esquema}{punto}lc_calificartipo lc4 on lc4.t_id =lc3.tipo_calificar 
left join {esquema}{punto}lc_grupocalificacion lg on lg.lc_calificacion_convencional =lc3.t_id 
left join {esquema}{punto}lc_clasecalificaciontipo lc5 on lc5.t_id =lg.clase_calificacion 
left join {esquema}{punto}lc_estadoconservaciontipo le on le.t_id =lg.conservacion 
left join {esquema}{punto}lc_objetoconstruccion lo on lo.lc_grupo_calificacion =lg.t_id 
left join {esquema}{punto}lc_objetoconstrucciontipo lo2 on lo2.t_id =lo.tipo_objeto_construccion 
where 1=1
and lc2.ilicode ='Convencional'
--and lu2.ilicode ='Institucional'
and lc3.t_id is not null
order by lp.numero_predial, lc.identificador 
),
tb_cond_4_9_a_18_y_20 as(
select 
b.*
,case when vp.puntos=b.puntos then 'Ok' else 'Fail' end as cond_4_9_a_18_y_20
from base b 
left join validacion_puntos vp on b.tipo_calificar=vp.calificar_tipo and b.tipo_objeto=vp.objetotipo
)
select * from tb_cond_4_9_a_18_y_20
where cond_4_9_a_18_y_20='Fail'