--regla3.6

with base as(
select 
distinct
lp.numero_predial_nacional
,lc.identificador 
,cu2.ilicode tipo_unidad_construccion 
,cuu.ilicode uso 
,lc.anio_construccion 
,lc2.total_calificacion 
,caa.ilicode tipo_anexo 
,ttp.ilicode tipo_tipologia  
, case 	when length (trim(identificador))= 1 then ascii(trim(identificador))-64 
		when length (trim(identificador))= 2 then (ascii(substring(identificador,1,1))-64)*26 + ascii(substring(identificador,2,1))-64 
		end letter_number
from {esquema}{punto}ilc_predio lp
inner join {esquema}{punto}col_uebaunit cu on cu.baunit =lp.t_id and cu.ue_cr_unidadconstruccion  is not null
inner join {esquema}{punto}cr_unidadconstruccion lu on lu.t_id =cu.ue_cr_unidadconstruccion 
left join {esquema}{punto}ilc_caracteristicasunidadconstruccion lc on lc.t_id =lu.cr_caracteristicasunidadconstruccion
left join {esquema}{punto}cr_unidadconstrucciontipo cu2 on cu2.t_id = lc.tipo_unidad_construccion
left join {esquema}{punto}cuc_calificacion_unidadconstruccion ccu on ccu.ilc_caracteristicasunidadconstruccion=lc.t_id
left join {esquema}{punto}cuc_calificacionconvencional lc2 on lc2.t_id =ccu.cuc_clfccnndcnstrccion_cuc_calificacionconvencional
left join {esquema}{punto}cuc_tipologianoconvencional lc3 on lc3.t_id =ccu.cuc_clfccnndcnstrccion_cuc_tipologianoconvencional
left join {esquema}{punto}cuc_tipologiaconstruccion lt on lt.t_id =ccu.cuc_clfccnndcnstrccion_cuc_tipologiaconstruccion 
left join {esquema}{punto}cr_usouconstipo cuu on cuu.t_id=lc.uso
left join {esquema}{punto}cuc_anexotipo caa on caa.t_id=lc3.tipo_anexo
left join {esquema}{punto}cuc_tipologiatipo ttp on ttp.t_id=lt.tipo_tipologia 
order by lp.numero_predial_nacional, lc.identificador )
, base2 as (select *
, row_number () over (partition by numero_predial_nacional)
, case 	when length (trim(identificador))= 1 and ascii(identificador)-64  = row_number () over (partition by numero_predial_nacional order by numero_predial_nacional, letter_number ) then 'Ok' 
		 when length (trim(identificador))= 2 and (ascii(substring(identificador,1,1))-64)*26 + ascii(substring(identificador,2,1))-64 = row_number () over (partition by numero_predial_nacional order by numero_predial_nacional, letter_number ) then 'Ok' 
		 else 'Fail' 
		 end regla_3_6
from base
order by (numero_predial_nacional, base.identificador, row_number () over (partition by numero_predial_nacional)))
select *
from base2
where numero_predial_nacional in (select numero_predial_nacional 
						from base2 
						where regla_3_6= 'Fail')
order by numero_predial_nacional, letter_number


