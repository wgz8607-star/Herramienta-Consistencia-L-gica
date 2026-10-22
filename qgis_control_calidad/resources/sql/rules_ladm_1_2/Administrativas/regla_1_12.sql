--cond 1.12

with tb_cond_1_12 as(
select 
lp.numero_predial
,lp.tiene_fmi 
,lp.codigo_orip
,lp.matricula_inmobiliaria 
,case when lp.tiene_fmi =true and 
		   codigo_orip <>'' and 
		   codigo_orip is not null and 
		   matricula_inmobiliaria <>'' and 
		   matricula_inmobiliaria is not null 
	  	then 'OK' 
	  when lp.tiene_fmi =false  and 
		   codigo_orip is null and 
		   matricula_inmobiliaria is null 
		then 'OK'
	  else 'Fail' end as cond_1_12
from {esquema}{punto}lc_predio lp 
)
select * from tb_cond_1_12 
where cond_1_12 ='Fail';
