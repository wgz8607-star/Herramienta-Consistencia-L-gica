with tb_nombres as(
select 
distinct
li.primer_nombre 
,li.segundo_nombre 
,li.primer_apellido 
,li.segundo_apellido 
,li.documento_identidad 
from {esquema}.lc_interesado li 
where li.primer_nombre is not null or li.segundo_nombre is not null or li.primer_apellido is not null or li.segundo_apellido is not null
),
tb_nombres_2 as(
select 
*, count(*)over(partition by primer_nombre, segundo_nombre, primer_apellido, segundo_apellido) conteo
from tb_nombres
),
tb_nombres_3 as
(
select * from tb_nombres_2 where conteo>1
),
tb_nombre as(
select 
distinct
li.nombre 
,li.documento_identidad 
from {esquema}.lc_interesado li 
where li.primer_nombre is null and li.segundo_nombre is null and li.primer_apellido is null and li.segundo_apellido is null and li.razon_social is null
),
tb_nombre_2 as
(
select 
*, count(*)over(partition by nombre) conteo
from tb_nombre
),
tb_nombre_3
as(
select * from tb_nombre_2 where conteo>1
)
,tb_rz as(
select 
distinct
li.razon_social 
,li.documento_identidad 
from {esquema}.lc_interesado li 
where li.razon_social is not null
),
tb_rz_2 as(
select *, count(*)over(partition by razon_social) conteo
from tb_rz
),
tb_rz_3 as(
select * from tb_rz_2 where conteo>1
),
tb_cond_2_39 as (
select primer_nombre, segundo_nombre, primer_apellido ,segundo_apellido,null as nombre, null as rz,documento_identidad  from tb_nombres_3
union all
select null primer_nombre, null segundo_nombre, null primer_apellido ,null segundo_apellido, nombre, null as rz,documento_identidad  from tb_nombre_3
union all
select null primer_nombre, null segundo_nombre, null primer_apellido ,null segundo_apellido,null nombre, razon_social ,documento_identidad  from tb_rz_3
)
select *, 'Fail' as cond_2_39 from tb_cond_2_39
order by primer_nombre , segundo_nombre , primer_apellido , segundo_apellido , nombre, rz
