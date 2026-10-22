--cond 1.24
with 
col_uebaunit_terreno as 
(select distinct cu2.ue_lc_terreno, cu2.baunit  from {esquema}.col_uebaunit cu2 
 where cu2.ue_lc_servidumbretransito is null 
   and cu2.ue_lc_construccion is null 
   and cu2.ue_lc_unidadconstruccion is null
),
tb_cond_1_24_1 as 
(
select 
lp.numero_predial
,lc.ilicode condicion_predio
,cu.ue_lc_terreno 
,le.numero_predial 
,case when le.numero_predial is not null then 'OK'
	  when cu.ue_lc_terreno is not null then 'OK' 
	  else 'Fail' end as cond_1_24_1
from {esquema}.lc_predio lp
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio 
left join {esquema}.lc_estructuranovedadnumeropredial le on le.numero_predial =lp.numero_predial 
												  and le.tipo_novedad =(select t_id from {esquema}.lc_estructuranovedadnumeropredial_tipo_novedad letn where letn.ilicode='Cancelacion')
left join col_uebaunit_terreno cu on cu.baunit=lp.t_id  
where lc.ilicode in (
'NPH','PH.Matriz','Condominio.Matriz',
'Condominio.Unidad_Predial','Parque_Cementerio.Matriz',
'Via','Bien_Uso_Publico')
)
,
tb_cond_1_24_2 as
(
select 
null,
null, 
lt.t_id,
null,
'Fail'
from {esquema}.lc_terreno lt
left join {esquema}.col_uebaunit cu3 on cu3.ue_lc_terreno =lt.t_id 
where cu3.t_id is null
)
select * from tb_cond_1_24_1
where cond_1_24_1 ='Fail'
union all 
select * from tb_cond_1_24_2;
