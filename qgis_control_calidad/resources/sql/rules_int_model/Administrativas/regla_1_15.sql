--Regla 1.15 

with tb1 as(
select ip.numero_predial_nacional npn, 
case when cu2.t_id is not null then 1 else 0 end as conteoconst
from {esquema}{punto}ilc_predio ip 
left join {esquema}{punto}col_uebaunit cu on cu.baunit = ip.t_id 
right join {esquema}{punto}cr_unidadconstruccion cu2 on cu2.t_id =cu.ue_cr_unidadconstruccion 
)
select ip2.numero_predial_nacional,id.ilicode destinacion, sum(tb1.conteoconst)sumaconst, 'Fail' condi_1_15
from {esquema}{punto}ilc_predio ip2
left join {esquema}{punto}ilc_destinacioneconomicatipo id ON id.t_id = ip2.destinacion_economica 
left join tb1 on tb1.npn = ip2.numero_predial_nacional
where tb1.conteoconst >0 and id.ilicode IN ('Lote_Urbanizable_No_Urbanizado','Lote_Urbanizado_No_Construido','Lote_No_Urbanizable')
group by ip2.numero_predial_nacional, id.ilicode
having sum(tb1.conteoconst)>0