with tb_cond_1_25
as 
(
select 
lp.numero_predial
,lc.ilicode condicion
,lp2.numero_predial matriz
,f.numerador
,f.denominador
,sum((f.numerador/f.denominador)::numeric) over (partition by lpc.copropiedad) suma_copropiedad,
case when abs(sum((f.numerador/f.denominador)::numeric) over (partition by lpc.copropiedad)-1)>0.001 then 'Fail'
when f.t_id is null then 'Fail'
else 'OK' end as cond_1_25
from {esquema}.lc_predio lp
inner join {esquema}.lc_condicionprediotipo lc on lc.t_id =lp.condicion_predio
left join {esquema}.lc_predio_copropiedad lpc on lpc.predio =lp.t_id 
left join {esquema}.lc_predio lp2 on lp2.t_id =lpc.copropiedad 
left join {esquema}.fraccion f ON f.lc_predio_copropiedad_coeficiente=lpc.t_id
where lc.ilicode in ('PH.Unidad_Predial','Condominio.Unidad_Predial')
)
select * from tb_cond_1_25
where cond_1_25 ='Fail'
order by matriz,numero_predial;
