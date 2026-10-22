--cond 1.28 (nueva) 
SELECT  lp.numero_predial ,'Fail' cond_1_28 FROM {esquema}{punto}lc_predio lp 
left join {esquema}{punto}lc_predio lp2 on left(lp.numero_predial,22)=left(lp2.numero_predial,22)  and right(lp2.numero_predial,8)='00000000'
WHERE substring(lp.numero_predial,22,1) in ('8','9') and right(lp.numero_predial,8)<>'00000000'
and lp2.numero_predial is null
