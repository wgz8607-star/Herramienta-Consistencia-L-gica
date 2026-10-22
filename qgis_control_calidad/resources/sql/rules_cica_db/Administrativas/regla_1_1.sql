-- regla 1.1
WITH t_a as(
SELECT numero_predial
FROM {esquema}.cica_predio cp
WHERE cp.estado = 'ACTIVO'
AND cp.etapa IN ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')
)
,tb_1 AS (
SELECT
distinct
cp.numero_predial,
cp.condicion_predio_tipo,
CASE
WHEN cp.condicion_predio_tipo = 'NPH' and substring(cp.numero_predial, 22, 9) = '000000000' THEN 'Ok'
WHEN cp.condicion_predio_tipo = 'Informal' and substring(cp.numero_predial, 22, 9) = '200000000' THEN 'OK'
when cp.condicion_predio_tipo = 'Bien_Uso_Publico' and substring(cp.numero_predial, 22, 9) = '300000000' THEN 'Ok'
when cp.condicion_predio_tipo = 'Vía' and substring(cp.numero_predial, 22, 9) = '400000000' THEN 'Ok'
when cp.condicion_predio_tipo = 'Condominio.Matriz' and substring(cp.numero_predial, 22, 9) = '800000000' THEN 'Ok'
when cp.condicion_predio_tipo = 'PH.Matriz' and substring(cp.numero_predial, 22, 9) = '900000000' THEN 'Ok'
when cp.condicion_predio_tipo = 'Matriz' and substring(cp.numero_predial, 22, 9) = '900000000' THEN 'Ok'
when cp.condicion_predio_tipo = 'Parque_Cementerio.Matriz' and substring(cp.numero_predial, 22, 9) = '700000000' THEN 'Ok'
when cp.condicion_predio_tipo = 'PH.Unidad_Predial' and substring(cp.numero_predial, 22, 1) = '9' and substring(cp.numero_predial, 23, 8) <> '00000000' THEN 'Ok'
when cp.condicion_predio_tipo = 'Condominio.Unidad_Predial' and substring(cp.numero_predial, 22, 1) = '8' and substring(cp.numero_predial, 23, 8) <> '00000000' THEN 'Ok'
when cp.condicion_predio_tipo in ('Mejora','Mejora.PH','Mejora.NPH') then 'Fail'
ELSE 'Fail'
END AS cond_1_1
FROM {esquema}.cica_predio cp
)
,regla AS (
SELECT
tb_1.numero_predial,
tb_1.condicion_predio_tipo,
tb_1.cond_1_1,
'Condicion predio mal diligenciada respecto NPN' observacion
FROM tb_1 inner join t_a on tb_1.numero_predial = t_a.numero_predial
WHERE tb_1.cond_1_1 = 'Fail'
)
,t_numdup as(
select numero_predial,null,'Fail','NPN duplicado' from t_a
group by 1 having count(*)>1
)
,datos_control AS (
SELECT DISTINCT ON (csc.numero_predial) -- <- Esto evita duplicados por predio
csc.numero_predial,
csc.coordinador,
csc.reconocedor
FROM {esquema}.cica_seguimiento_control csc
)
select
regla.numero_predial,
regla.condicion_predio_tipo,
regla.cond_1_1,
regla.observacion,
datos_control.coordinador,
datos_control.reconocedor
from (select * from regla union select * from t_numdup) regla
left join datos_control ON regla.numero_predial = datos_control.numero_predial;