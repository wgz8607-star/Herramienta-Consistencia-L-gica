with base as(
select lp.numero_predial
,lo.fecha_captura_oferta 
,ld.fecha_visita_predial 
,case when  lo.fecha_captura_oferta >ld.fecha_visita_predial then 'Fail' else 'Ok' end as cond_4_27
from {esquema}{punto}lc_predio lp 
inner join {esquema}{punto}lc_ofertasmercadoinmobiliario lo on lo.lc_predio =lp.t_id 
left join  {esquema}{punto}lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
)
select * from base
where cond_4_27='Fail'