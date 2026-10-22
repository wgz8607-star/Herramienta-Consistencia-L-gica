--cond 1_.2 (nueva) 
SELECT  lp.numero_predial, 'Fail' cond_1_2 FROM {esquema}{punto}lc_predio lp WHERE length(lp.numero_predial)<>30
