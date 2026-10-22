with tb_cond_1_25
as 
(
select 
lp.numero_predial
,lc.ilicode condicion
,lp2.numero_predial matriz
,lpc.coeficiente
,sum(lpc.coeficiente) over (partition by lpc.matriz) suma_copropiedad,
case when abs(sum(lpc.coeficiente) over (partition by lpc.matriz)-1)>0.001 then 'Fail'
when coeficiente=0 or coeficiente is null then 'Fail'
else 'OK' end as cond_1_25
from {esquema}{punto}lc_predio lp
inner join {esquema}{punto}lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio
left join {esquema}{punto}lc_predio_copropiedad lpc on lpc.unidad_predial =lp.t_id 
left join {esquema}{punto}lc_predio lp2 on lp2.t_id =lpc.matriz 
where lc.ilicode in ('PH.Unidad_Predial','Condominio.Unidad_Predial')
)
select * from tb_cond_1_25
where cond_1_25 ='Fail'
order by matriz,numero_predial;
