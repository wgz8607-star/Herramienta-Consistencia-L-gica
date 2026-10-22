with base as(
select 
distinct
lp.numero_predial
,lu.identificador 
,lc2.ilicode tipo_construccion
,lu2.ilicode tipo_unidad
--,la.ilicode tipo_anexo
,lc4.ilicode tipo_calificar
--,lc3.t_id
,lc3.total_calificacion 
,lc5.ilicode clase_calificacion
,le.ilicode conservacion
,SPLIT_PART(lo2.ilicode, '.', 1) tipo_objeto
,lo2.ilicode tipo_objeto_2
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}.lc_construcciontipo lc2 on lc2.t_id =lu.tipo_construccion 
left join {esquema}.lc_unidadconstrucciontipo lu2 on lu2.t_id =lu.tipo_unidad_construccion 
left join {esquema}.lc_usouconstipo lu3 on lu3.t_id =lu.uso 
left join {esquema}.lc_calificacionconvencional lc3 on lc3.lc_unidad_construccion =lu.t_id 
left join {esquema}.lc_calificartipo lc4 on lc4.t_id =lc3.tipo_calificar 
left join {esquema}.lc_grupocalificacion lg on lg.lc_calificacion_convencional =lc3.t_id 
left join {esquema}.lc_clasecalificaciontipo lc5 on lc5.t_id =lg.clase_calificacion 
left join {esquema}.lc_estadoconservaciontipo le on le.t_id =lg.conservacion 
left join {esquema}.lc_objetoconstruccion lo on lo.lc_grupo_calificacion =lg.t_id 
left join {esquema}.lc_objetoconstrucciontipo lo2 on lo2.t_id =lo.tipo_objeto_construccion 
where 1=1
and lc2.ilicode ='Convencional'
--and lu2.ilicode ='Institucional'
and lc3.t_id is not null
--and lp.numero_predial ='708230100000000080001000000000'
--and lc.identificador ='A'
order by lp.numero_predial, lu.identificador 
),
validacion_construccion (tipo_unidad,clase_calificacion, tipos_construccion) AS (
  VALUES
    ('Residencial','Estructura', 'Armazon,Cubierta,Muros'),
    ('Residencial','Acabados_Principales', 'Cubrimiento_Muros,Fachada,Piso'),
    ('Residencial','Banio', 'Enchape_Banio,Mobiliario_Banio,Tamanio_Banio'),
    ('Residencial','Cocina', 'Enchape_Cocina,Mobiliario_Cocina,Tamanio_Cocina'),
    ('Residencial','Complemento_Industria', 'Cerchas_Complemento_Industria'),
    ('Comercial','Estructura', 'Armazon,Cubierta,Muros'),
    ('Comercial','Acabados_Principales', 'Cubrimiento_Muros,Fachada,Piso'),
    ('Comercial','Banio','Mobiliario_Banio'),
    ('Comercial','Cocina','Mobiliario_Cocina'),
    ('Institucional','Estructura', 'Armazon,Cubierta,Muros'),
    ('Institucional','Acabados_Principales', 'Cubrimiento_Muros,Fachada,Piso'),
    ('Institucional','Banio','Mobiliario_Banio'),
    ('Institucional','Cocina','Mobiliario_Cocina'),
    ('Industrial','Estructura', 'Armazon,Cubierta,Muros'),
    ('Industrial','Acabados_Principales', 'Cubrimiento_Muros,Fachada,Piso'),
    ('Industrial','Complemento_Industria', 'Cerchas_Complemento_Industria')    
)
,tb_agrup as(
select 
numero_predial
,tipo_unidad
,identificador
,clase_calificacion
,string_agg(tipo_objeto,',' order by tipo_objeto) objetos
from base
group by numero_predial,identificador,clase_calificacion,tipo_unidad
)
,tb_cond_4_8 as(
select ta.*
,case when ta.objetos<>vc.tipos_construccion then 'Fail' else 'Ok' end as cond_4_8
from tb_agrup ta 
left join validacion_construccion vc on ta.clase_calificacion=vc.clase_calificacion and ta.tipo_unidad=vc.tipo_unidad
)
select tt.* from tb_cond_4_8 tt
left join (select * from base where tipo_objeto_2 in ('Tamanio_Banio.Sin_Banio','Tamanio_Cocina.Sin_Cocina')) q on q.numero_predial=tt.numero_predial 
																												and q.identificador=tt.identificador
																												and q.tipo_unidad=tt.tipo_unidad
																												and q.clase_calificacion=tt.clase_calificacion
																												and q.tipo_objeto=tt.objetos
where cond_4_8='Fail'
and q.numero_predial is null
order by numero_predial, identificador