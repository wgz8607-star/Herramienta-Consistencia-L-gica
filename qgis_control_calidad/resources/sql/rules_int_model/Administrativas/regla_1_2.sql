--Regla 1.2
with regla_30_dig as(
	select ip.numero_predial_nacional,
		'longitud npn: '||length(ip.numero_predial_nacional)::text info,
		'ilc_predio' tabla ,
		'Fail' cond_1_2,
		'Longitud numero_predial diferente de 30 digitos' descripcion
	from {esquema}{punto}ilc_predio ip
	where length(ip.numero_predial_nacional)<>30 
	union 
	select
		ie.numero_predial novedadnumeropredial,
		'longitud npn: '||length(ie.numero_predial)::text lennovedd, 
		'ilc_estructuranovedadnumeropredial' tabla ,
		'Fail' cond_1_2,
		'Longitud numero_predial diferente de 30 digitos' descripcion
	from 
	{esquema}{punto}ilc_estructuranovedadnumeropredial ie
	where length(ie.numero_predial)<>30 
)

select * from regla_30_dig