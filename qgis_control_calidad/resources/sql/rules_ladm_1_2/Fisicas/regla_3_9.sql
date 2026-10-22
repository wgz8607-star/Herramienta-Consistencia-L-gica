
with base as(
select
distinct
lp.numero_predial 
, lc.identificador  
, lc.tipo_dominio 
, lc.tipo_construccion 
, lc.tipo_unidad_construccion 
, lc.tipo_planta 
, lc.total_habitaciones 
, lc.total_banios 
, lc.total_locales 
, lc.uso 
, lc.anio_construccion 
, lc2.tipo_calificar 
, lc2.total_calificacion 
, lc3.tipo_anexo 
, lt.tipo_tipologia 
, lt.cual 
, case 	when length (trim(identificador))= 1 then ascii(trim(identificador))-64 
		when length (trim(identificador))= 2 then (ascii(substring(trim(identificador),1,1))-64)*26 + ascii(substring(trim(identificador),2,1))-64 
		end letter_number
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_lc_unidadconstruccion  is not null
inner join {esquema}{punto}lc_unidadconstruccion lu on lu.t_id =cu.ue_lc_unidadconstruccion 
left join {esquema}{punto}lc_caracteristicasunidadconstruccion lc on lc.t_id =lu.lc_caracteristicasunidadconstruccion
left join {esquema}{punto}lc_unidadconstrucciontipo lu2 on lc.tipo_unidad_construccion = lu2.t_id 
left join {esquema}{punto}lc_calificacionconvencional lc2 on lc2.lc_unidad_construccion = lc.t_id 
left join {esquema}{punto}lc_calificacionnoconvencional lc3 on lc3.lc_unidad_construccion = lc.t_id 
left join {esquema}{punto}lc_tipologiaconstruccion lt on lt.lc_unidad_construccion = lc.t_id 
order by lp.numero_predial, case 	when length (trim(identificador))= 1 then ascii(trim(identificador))-64 
		when length (trim(identificador))= 2 then (ascii(substring(trim(identificador),1,1))-64)*26 + ascii(substring(trim(identificador),2,1))-64 
		end 
		)
, base2 as (
select *
, row_number () over (partition by numero_predial)
, case 	when length (trim(identificador))= 1 and ascii(trim(identificador))-64  = row_number () over (partition by numero_predial order by numero_predial, letter_number ) then 'Ok' 
		 when length (trim(identificador))= 2 and (ascii(substring(trim(identificador),1,1))-64)*26 + ascii(substring(trim(identificador),2,1))-64 = row_number () over (partition by numero_predial order by numero_predial, letter_number ) then 'Ok' 
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