--cond 1.27 (nueva) 
SELECT  lp.numero_predial, 'Fail' cond_1_27 FROM {esquema}{punto}lc_predio lp 
left join {esquema}{punto}lc_predio lp2 on left(lp.numero_predial,22)=left(lp2.numero_predial,22) and lp.numero_predial<>lp2.numero_predial 
WHERE substring(lp.numero_predial,22,9) in ('800000000','900000000')
group by lp.numero_predial
having count(*)<2