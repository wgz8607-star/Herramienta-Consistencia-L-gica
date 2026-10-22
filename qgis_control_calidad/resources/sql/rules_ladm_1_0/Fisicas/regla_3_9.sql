

with base as(
select
distinct
lp.numero_predial 
, lu.identificador  
, lu.tipo_dominio 
, lu.tipo_construccion 
, lu.tipo_unidad_construccion 
, lu.tipo_planta 
, lu.total_habitaciones 
, lu.total_banios 
, lu.total_locales 
, lu.uso 
, lu.anio_construccion 
, lc2.tipo_calificar 
, lc2.total_calificacion 
, lc3.tipo_anexo 
, lt.tipo_tipologia 
, case 	when length (trim(identificador))= 1 then ascii(trim(identificador))-64 
		when length (trim(identificador))= 2 then (ascii(substring(identificador,1,1))-64)*26 + ascii(substring(identificador,2,1))-64 
		end letter_number
from {esquema}.lc_predio lp
inner join {esquema}.col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}.lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion  
left join {esquema}.lc_calificacionconvencional lc2 on lc2.lc_unidad_construccion =lu.t_id 
left join {esquema}.lc_calificacionnoconvencional lc3 on lc3.lc_unidad_construccion =lu.t_id 
left join {esquema}.lc_tipologiaconstruccion lt on lt.lc_unidad_construccion =lu.t_id 
order by lp.numero_predial, lu.identificador )
, base2 as (select *
, row_number () over (partition by numero_predial)
, case 	when length (trim(identificador))= 1 and ascii(identificador)-64  = row_number () over (partition by numero_predial order by numero_predial, letter_number ) then 'Ok' 
		 when length (trim(identificador))= 2 and (ascii(substring(identificador,1,1))-64)*26 + ascii(substring(identificador,2,1))-64 = row_number () over (partition by numero_predial order by numero_predial, letter_number ) then 'Ok' 
		 else 'Fail' 
		 end regla_3_9
from base
order by (base.numero_predial, base.letter_number, row_number () over (partition by base.numero_predial)))
select *
from base2
where numero_predial in (select numero_predial 
						from base2 
						where regla_3_9= 'Fail')
order by numero_predial, letter_number