with tb1 as (
--1
select 1 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where substring(cp.numero_predial,22,1) in ('0','2','3','4','7')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--2
select 2 id, count(cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp
where cp.condicion_predio_tipo = 'Matriz'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--3
select 3 id, count(cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp
where cp.condicion_predio_tipo = 'PH.Unidad_Predial'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--4
select 4 id, count(cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp
where cp.condicion_predio_tipo = 'Condominio.Matriz'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--5
select 5 id, count(cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp
where cp.condicion_predio_tipo = 'Condominio.Unidad_Predial'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--6
select 6 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where substring(cp.numero_predial,22,1) in ('1','5','6')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--7
select 7 id, count (cpd.numero_predial)
from {esquema}{punto}cica_predio_derecho cpd 
left join {esquema}{punto} cica_predio cp on cpd.numero_predial = cp.numero_predial 
where cpd.estado = 'ACTIVO'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--8
select 8 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--9
select 9 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where NULLIF(cp.matricula,'') is not null
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all 
--10
select 10 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where NULLIF(cp.circulo_registral,'') is not null
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all 
--11
select 11 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.destino in ('R', 'S', 'T','AD')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all 
--12
select 12 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.destino in ('A', 'B', 'C', 'F', 'G', 'I', 'J', 'X')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all 
--13
select 13 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.destino in ('U','L','N','M','Z','O','AA','AC','W','R','S','D','R', 'S', 'T','AD')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all 
--14
select 14 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.tiene_fmi = 'NO'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all 
--15
select 15 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.condicion_predio_tipo in ('NPH', 'Matriz', 'Condominio.Unidad_Predial', 'Condominio.Matriz' )
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all 
--16
select 16 id, count (cc.numero_predial) Cantidad
from {esquema}{punto}cica_contacto cc 
left join {esquema}{punto} cica_predio cp on cc.numero_predial = cp.numero_predial
where NULLIF(cc.primer_nombre,'') || NULLIF(cc.primer_apellido,'') is not null
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--17
select 17 id, count (cc.numero_predial) Cantidad
from {esquema}{punto}cica_contacto cc 
left join  {esquema}{punto}cica_predio cp on cc.numero_predial = cp.numero_predial
where NULLIF(cc.numero_documento,'') is not null
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--18
select 18 id, count (cc.numero_predial) Cantidad
from {esquema}{punto}cica_contacto cc 
left join {esquema}{punto} cica_predio cp on cc.numero_predial = cp.numero_predial
where cc.estado = 'ACTIVO'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--19
select 19 id, count (cc.numero_predial) Cantidad
from {esquema}{punto}cica_contacto cc 
left join {esquema}{punto} cica_predio cp on cc.numero_predial = cp.numero_predial
where cc.estado = 'ACTIVO'
and NULLIF(cc.celular,'') is not null
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--20
select 20 id, count (cc.numero_predial) Cantidad
from {esquema}{punto}cica_contacto cc 
left join  {esquema}{punto}cica_predio cp on cp.numero_predial = cc.numero_predial
where nullif(cc.correo_electronico,'') is not null
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--21
select 21 id, count (cc.numero_predial) Cantidad
from {esquema}{punto}cica_contacto cc 
left join  {esquema}{punto}cica_predio cp on cp.numero_predial = cc.numero_predial
where cc.autorizacion_notificacion = 'SI'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--22
select 22 id, count (cc.numero_predial) Cantidad
from {esquema}{punto}cica_contacto cc 
left join  {esquema}{punto}cica_predio cp on cp.numero_predial = cc.numero_predial
where nullif(cc.direccion,'') is not null
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--23
select 23 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.condicion_predio_tipo = 'PH.Unidad_Predial'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all 
--24
select 24 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where substring(cp.numero_predial, 22, 1) <> '2'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--25
select 25 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto} cica_predio_derecho cpd on cp.numero_predial = cpd.numero_predial
where cp.tipo_predio ='Privado'
and cpd.tipo_derecho = 'Dominio'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--26
select 26 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto} cica_predio_derecho cpd on cp.numero_predial = cpd.numero_predial
where cpd.tipo_derecho = 'Posesión'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--27
select 27 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.tipo_predio ='Privado'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--28
select 28 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.tipo_predio in ('Publico.Patrimonial', 'Publico.Fiscal', 'Publico.Baldio', 'Publico.Uso_Publico','Presunto_Baldio')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--29
select 29 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto} cica_predio_derecho cpd on cp.numero_predial = cpd.numero_predial
where cp.tipo_predio in ('Publico.Baldio','Presunto_Baldio','Publico.Fiscal', 'Publico.Uso_Publico','Publico.Patrimonial')
and cpd.tipo_derecho = 'Dominio'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--30
select 30 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.tipo_predio = 'Territorio_Colectivo'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--31
select 31 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto} cica_predio_derecho cpd on cp.numero_predial = cpd.numero_predial
where cp.tipo_predio in ('Publico.Baldio','Presunto_Baldio')
and cpd.tipo_derecho = 'Ocupación'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--32
select 32 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where length(cp.matricula)>7
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--33
select 33 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.tiene_fmi = 'SI'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--34
select 34 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_propietario cp
left join {esquema}{punto} cica_predio cp2 on cp.numero_predial = cp2.numero_predial
where cp.tipo_persona = 'JURIDICA'
and cp2.estado = 'ACTIVO'
and cp2.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--35
select 35 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_propietario cp
left join {esquema}{punto} cica_predio cp2 on cp.numero_predial = cp2.numero_predial
where cp.tipo_persona = 'NATURAL'
and cp2.estado = 'ACTIVO'
and cp2.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--36
select 36 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_propietario cp
left join {esquema}{punto} cica_predio cp2 on cp.numero_predial = cp2.numero_predial
where cp.tipo_documento in ('CC', 'CE', 'P', 'TI', 'RC', 'NUIP')
and cp2.estado = 'ACTIVO'
and cp2.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--37
select 37 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_propietario cp
left join {esquema}{punto} cica_predio cp2 on cp.numero_predial = cp2.numero_predial
where cp.tipo_documento = 'NIT'
and cp2.estado = 'ACTIVO'
and cp2.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--38
select 38 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_propietario cp
left join {esquema}{punto} cica_predio cp2 on cp.numero_predial = cp2.numero_predial
where cp2.estado = 'ACTIVO'
and cp2.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--39
select 39 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_propietario cp
left join {esquema}{punto} cica_predio cp2 on cp.numero_predial = cp2.numero_predial
where cp.grupo_interesado = 'Grupo_Mixto'
and cp2.estado = 'ACTIVO'
and cp2.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--40
select 40 id, count (cj.numero_predial) Cantidad
from {esquema}{punto}cica_justificacion cj
left join {esquema}{punto} cica_predio cp on cj.numero_predial = cp.numero_predial
where cj.tipo_documento in ('Escritura_Publica', 'Sentencia_Judicial', 'Acto_Administrativo')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--41
select 41 id, count (cj.numero_predial) Cantidad
from {esquema}{punto}cica_justificacion cj
left join {esquema}{punto} cica_predio cp on cj.numero_predial = cp.numero_predial
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--42
select 42 id, count (cj.numero_predial) Cantidad
from {esquema}{punto}cica_justificacion cj
left join {esquema}{punto} cica_predio cp on cj.numero_predial = cp.numero_predial
where cj.tipo_documento in  ('Escritura_Publica', 'Sentencia_Judicial')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--43
select 43 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.condicion_predio_tipo = 'Informal'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--44
select 44 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.condicion_predio_tipo = 'PH.Unidad'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--45
select 45 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto} cica_unidad_construccion cuc on cuc.numero_predial = cp.numero_predial
where cp.condicion_predio_tipo in ('PH', 'Condominio')
and cuc.tipo_calificacion in ('RESIDENCIAL', 'COMERCIAL', 'INSTITUCIONAL', 'INDUSTRIAL')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--46
select 46 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto} cica_unidad_construccion cuc on cuc.numero_predial = cp.numero_predial
where cp.condicion_predio_tipo not in ('PH', 'Condominio')
and cuc.tipo_calificacion in ('RESIDENCIAL', 'COMERCIAL', 'INSTITUCIONAL', 'INDUSTRIAL')
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--47
(with union_capas_1 as (
	select codigo
	from {esquema}{punto}u_terreno_ctm12 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}u_terreno_informal 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}r_terreno_ctm12 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}r_terreno_informal
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	)
select 47 id, count (codigo) Cantidad
from union_capas_1)
union all 
--48
(with union_capas_2 as (
	select codigo
	from {esquema}{punto}u_terreno_ctm12 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}u_terreno_informal 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}r_terreno_ctm12 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}r_terreno_informal
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}u_unidad_ctm12  
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	and substring(codigo, 22, 1) = '9'
and substring (codigo, 27,4)='0000'
	union all 
	select codigo
	from {esquema}{punto}u_unidad_informal  
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	and substring(codigo, 22, 1) = '9'
and substring (codigo, 27,4)='0000'
	union all 
	select codigo
	from {esquema}{punto}r_unidad_ctm12  
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	and substring(codigo, 22, 1) = '9'
and substring (codigo, 27,4)='0000'
	union all 
	select codigo
	from {esquema}{punto}r_unidad_informal  
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	and substring(codigo, 22, 1) = '9'
and substring (codigo, 27,4)='0000'
	)
select 48 id, count (codigo) Cantidad
from union_capas_2
)
union all 
--49
(with union_capas_3 as (
	select codigo
	from {esquema}{punto}u_unidad_ctm12 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}u_unidad_informal 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}r_unidad_ctm12 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}r_unidad_informal
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	)
select 49 id, count (codigo) Cantidad
from union_capas_3)
union all 
--50
select 50 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.destino = 'A'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--51
select 51 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.destino = 'C'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--52
select 52 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
where cp.destino = 'B'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--53
select 53 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_unidad_construccion cuc
left join {esquema}{punto}cica_predio cp on cuc.numero_predial = cp.numero_predial
where cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--54
(with union_capas_4 as (
	select codigo
	from {esquema}{punto}u_unidad_ctm12 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}u_unidad_informal 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}r_unidad_ctm12 
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	union all 
	select codigo
	from {esquema}{punto}r_unidad_informal
	left join {esquema}{punto} cica_predio cp on codigo = cp.numero_predial
	where cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
	)
select 54 id, count (codigo) Cantidad
from union_capas_4)
union all
--55
select 55 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto} cica_unidad_construccion cuc on cuc.numero_predial = cp.numero_predial
where cuc.tipo_construccion = 'CONVENCIONAL'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
union all
--56
select 56 id, count (cp.numero_predial) Cantidad
from {esquema}{punto}cica_predio cp 
left join {esquema}{punto} cica_unidad_construccion cuc on cuc.numero_predial = cp.numero_predial
where cuc.tipo_construccion = 'NO_CONVENCIONAL'
and cp.estado = 'ACTIVO'
and cp.etapa in ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
),
tb2 as ( 
select * from (values(1, 'Registros de Datos_Predio donde el digito 22 de Datos_Predio.Numero Predial sea igual a 0 o 2 o 3 o 4 o 7 y con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,1'),
(2, 'Registros de Datos Predio donde Datos Predio.Condicion Predio Tipo = Matriz con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,4'),
(3, 'Registros de Datos Predio donde Datos Predio.Condicion Predio Tipo es PH.Unidad_Predial con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,5'),
(4, 'Registros de Datos Predio Datos  donde Datos Predio.Condicion Predio Tipo = Condominio.Matriz con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,6'),
(5, 'Registros de  Datos Predio donde Predio.Condicion Predio Tipo = Condominio.Unidad Predial con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,7'),
(6, 'Registros de Datos_Predio donde el digito 22 de Datos_Predio.Numero Predial sea igual a 1 o 5 o 6 con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,8'),
(7, 'Todos los registros de Datos Predio-Derecho en estado Activo con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.9 , 1.10 , 2,4'),
(8, 'Todos los registros de Datos Predio en estado Activo con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.12, 1.23, 2,38'),
(9, 'Todos los registros de Datos Predios con Datos Predio.Matricula diligenciado, que en Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.13 , 1.14 , 2,1, 2.16'),
(10, 'Registros de Datos Predio.Circulo Registral diligenciado con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.15'),
(11, 'Registros de Datos Predio.Destino = R,S,T,AD con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.16', '1,18'),
(12, 'Registros de Datos Predio.Destino = A, B, C, F, G, I, J, X con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,19'),
(13, 'Registros de Datos Predio.Destino = R, S y T con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,21'),
(14, 'Registros de Datos Predio.Tiene FMI = No con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,22'),
(15, 'Registros de Datos Predio.Condicion Predio Tipo  = NPH, Matriz ó Condominio.Matriz,  Condominio.Unidad_Predial con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,24'),
(16, 'Registros de Datos Contacto con Datos Contacto.Primer Nombre y Datos Contacto.Primer Apellido diligenciados con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1,49'),
(17, 'Registros de Datos Contacto con Datos Contacto.Numero Documento diligenciados y con estado Activo con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.50'),
(18, 'Todos los registros de Datos Contacto con estado Activo con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.51 , 1.55'),
(19, 'Registros de Datos Contacto con Datos Contacto.Celular diligenciados y con estado Activo con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.52'),
(20, 'Registros de Datos Contacto con Datos Contacto.Correo Electronico diligenciados con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.53'),
(21, 'Registros de Datos Contacto con Datos Contacto.Autoriza Notificacion = SI con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.54'),
(22, 'Registros de Datos Contacto con Datos Contacto.Direccion diligenciado con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.56'),
(23, 'Registros de Datos Predio con Datos Predio.Condicion Predio Tipo = PH.Unidad Predial  con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '1.60'),
(24, 'Registros de Datos_Predio donde el digito 22 de Datos_Predio.Numero Predial sea difrente a 2 y con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,5'),
(25, 'Registros con Datos Predio.Tipo Predio = “Privado” y  Datos Predio - Derecho.Tipo Derecho = “Dominio” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,6'),
(26, 'Datos Predio - Derecho.Tipo Derecho = “Posesion”  entonces Datos Predio.Tipo Predio = “Privado” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,7'),
(27, 'Datos Predio.Tipo Predio = “Privado”  con Datos Predio - Derecho.Tipo Derecho <> “Ocupación”   con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,8'),
(28, 'Datos Predio.Tipo Predio = “Publico.Baldio” ó “Publico.Fiscal” ó “Publico.Patrimonial” ó “Publico.Uso_Publico” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,9'),
(29, 'Datos Predio.Tipo Predio = “Publico.Baldio” y Datos Predio - Derecho.Tipo Derecho = “Dominio” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2.10, 2.13'),
(30, 'Datos Predio.Tipo Predio = Territorio_Colectivo con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2.11'),
(31, 'Datos Predio.Tipo Predio = “Publico.Baldio” y Datos Predio - Derecho.Tipo Derecho = “Ocupacion” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2.12'),
(32, 'Todos los registros de Datos Predios con longitud de Datos Predio.Matricula > 7 que en Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,17'),
(33, 'Registros de Datos Predio.Tiene FMI = Si con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,18'),
(34, 'Registros de Datos Propietarios donde Datos Propietarios.Tipo Persona = “JURIDICA” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2.20 , 2.25, 2.27'),
(35, 'Registros de Datos Propietarios donde Datos Propietarios.Tipo Persona = “NATURAL” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2.21 , 2.24 , 2.26, 2.29'),
(36, 'Registros de Datos Propietarios donde  Datos Propietarios. Tipo documento = “CC” ó “CE” ó P ó “TI” ó “RC” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2.22'),
(37, 'Registros de Datos Propietarios donde  Propietarios. Tipo documento = “NIT” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2.23'),
(38, 'Todos los registros de Datos Propietarios con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,28 , 2,32, 2,33, 2.37, 2,39, 2,40'),
(39, 'Registros de Datos Propietarios donde Datos Propietario.Grupo Interesado = Grupo_Mixto con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2.30'),
(40, 'Registros de Justificacion donde Justificacion.Tipo Documento = Escritura_Publica,  Sentencia_Judicial, Acto_Administrativo con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,34'),
(41, 'Todos los registros de Justificacion con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,35'),
(42, 'Registros de Justificacion donde Justificacion.Tipo Documento = Escritura_Publica,  Sentencia_Judicial con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,36'),
(43, 'Registros de Datos Predio con Datos Predio. Condicion Predio Tipo = Informal con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '2,41'),
(44, 'Registros de Datos Predio con Datos Predio. Condicion Predio Tipo = PH.Unidad con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3,1'),
(45, 'Datos Predio.Condicion Predio Tipo= “PH” ó “Condominio”, y Unidad de Construccion.Tipo Calificacion “Residencial”, “Comercial”, “Institucional”ó “Industrial” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3,3'),
(46, 'Datos Predio.Condicion Predio Tipo <> “PH” ó “Condominio”, y Unidad de Construccion.Tipo Calificacion “Residencial”, “Comercial”, “Institucional”ó “Industrial” con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3,4'),
(47, 'Registros en las capas geográficas U_TERRENO_CTM12, U_TERRENO_INFORMAL, R_TERRENO_CTM12, R_TERRENO_INFORMAL con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3,6, 3,8'),
(48, 'Registros en las capas geográficas  U_TERRENO_CTM12, U_TERRENO_INFORMAL, R_TERRENO_CTM12, R_TERRENO_INFORMAL mas los codigos de U_UNIDAD_CTM12, U_UNIDAD_INFORMAL, R_UNIDAD_CTM12,  R_UNIDAD_INFORMAL que en su digito 22 sea = 9 y sus digitos 27-30 <> 0000 con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3,7'),
(49, 'Registros en las capas geográficas  U_UNIDAD_CTM12, U_UNIDAD_INFORMAL, R_UNIDAD_CTM12,  R_UNIDAD_INFORMAL con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3,9, 3.17, 3,33, 3,35, 3,36'),
(50, 'Registros de Datos Predio donde Datos Predio.destino = A con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3.20'),
(51, 'Registros de Datos Predio donde Datos Predio.destino = C con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3,21'),
(52, 'Registros de Datos Predio donde Datos Predio.destino = B con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3,22'),
(53, 'Todos los registros de la Unidad  de Construccion con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3.25, 3.30'),
(54, 'Todos los registros de la Unidad  de Construccion mas todos los registros de las capas geográficas U_UNIDAD_CTM12, U_UNIDAD_INFORMAL, R_UNIDAD_CTM12, y R_UNIDAD_INFORMAL con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '3,31'),
(55, 'Registros de Unidad de Construccion.TipoConstruccion= CONVENCIONAL con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '4,1'),
(56, 'Registros de Unidad de Construccion.TipoConstruccion= NO CONVENCIONAL con Datos Predio.Estado = Activo y Datos Predio.Etapa = CONTROL_CALIDAD_GENERAL o CONTROL_CALIDAD_GRUPO', '4,2')
)q (id,descripcion,reglas_validacion_Afectadas))
select tb2.id, tb2.descripcion, tb1.cantidad, tb2.reglas_validacion_afectadas from tb1 inner join tb2 on tb1.id=tb2.id
order by tb2.id asc