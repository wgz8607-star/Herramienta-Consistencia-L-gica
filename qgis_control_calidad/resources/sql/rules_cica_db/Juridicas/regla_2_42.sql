--regla_2.42 AJUSTADA
with cond_2_42 as (
select cp.numero_predial,
cj.tipo_documento,
cp.coordinador,
cp.usuario as reconocedor,
cp.tipo_predio,
'Fail' as regla_2_42
from {esquema}{punto}cica_predio cp
left join {esquema}{punto}cica_justificacion cj on cp.numero_predial = cj.numero_predial
where (cp.estado = 'ACTIVO'
	and cp.etapa in ('CONTROL_CALIDAD_GENERAL','CONTROL_CALIDAD_GRUPO')
	and cj.tipo_documento is null
	and substring(cp.numero_predial,22,1) not in ('2','3')
	and substring(cp.numero_predial,22,9) not in ('900000000','800000000' )
	and cp.tipo_predio not in ('Presunto_Baldio','Publico.Uso_Publico')
	)
)
SELECT DISTINCT
    numero_predial,
    tipo_documento,
    reconocedor,
    coordinador,
    tipo_predio,
    'Fail' AS regla_2_42
FROM cond_2_42;