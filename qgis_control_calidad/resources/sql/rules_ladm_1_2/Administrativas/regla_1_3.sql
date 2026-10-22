--cond 1_.3 (nueva) 
SELECT  lp.numero_predial, 'Fail' cond_1_3 FROM {esquema}{punto}lc_predio lp WHERE substring(lp.numero_predial,14,4)='0000'
