--cond_1_43
with tb_cond_1_43 as
(
select 
e.es_direccion_principal,
e.lc_predio_direccion,
count(*) conteo
from {esquema}{punto}extdireccion e 
group by e.lc_predio_direccion, e.es_direccion_principal  
)
select 
lp.numero_predial,
'Fail' cond_1_43
from tb_cond_1_43 b inner join {esquema}{punto}lc_predio lp on lp.t_id =b.lc_predio_direccion
where conteo>1 and es_direccion_principal =true;
