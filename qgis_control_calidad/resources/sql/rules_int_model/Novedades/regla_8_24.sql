-- Regla 8.24: El número predial en la tabla de novedades debe corresponder al NPN registrado en ILC_Predio.
-- Falla cuando: hay discrepancia entre los NPNs de novedades y predios.
with tb1 as(
select ie.numero_predial np_novedad, split_part(ietn.ilicode,'_',1) tipo
 from {esquema}{punto}ilc_estructuranovedadnumeropredial ie 
left  join {esquema}{punto}ilc_estructuranovedadnumeropredial_tipo_novedad ietn ON ietn.t_id = ie.tipo_novedad 
)
select np_novedad, tipo, count(tipo) conteo, 'Fail' cond_8_24
 from tb1
where tipo = 'Cambio'
group by np_novedad, tipo
having count(tipo) > 1
