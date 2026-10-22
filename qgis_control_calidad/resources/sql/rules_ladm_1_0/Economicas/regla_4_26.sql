with base as(
select lp.numero_predial
,lo2.ilicode tipo_oferta
,lo.valor_pedido 
,lo.valor_negociado
,case when lo.valor_pedido is not null and lo.valor_negociado is not null and lo.valor_negociado>0 and lo.valor_pedido>0 then 'Ok' else 'Fail' end as cond_4_26
from {esquema}.lc_predio lp 
inner join {esquema}.lc_ofertasmercadoinmobiliario lo on lo.lc_predio =lp.t_id 
left join {esquema}.lc_ofertatipo lo2 on lo2.t_id =lo.tipo_oferta 
where lo2.ilicode in ('Venta','Arriendo')
)
select * from base
where cond_4_26='Fail'