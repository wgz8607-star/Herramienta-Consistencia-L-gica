select cf.ilicode, lf.ente_emisor, lp.numero_predial, 'Fail' Cond_2_36
from {esquema}{punto}lc_fuenteadministrativa lf 
left join {esquema}{punto}col_fuenteadministrativatipo cf on cf.t_id = lf.tipo  
left join {esquema}{punto}col_unidadfuente cu on cu.fuente_administrativa = lf.t_id 
left join {esquema}{punto}lc_predio lp on lp.t_id = cu.unidad 
where (cf.ilicode  = 'Documento_Publico.Escritura_Publica' and lf.ente_emisor not ilike '%notaria%')
or (cf.ilicode  = 'Documento_Publico.Sentencia_Judicial' and lf.ente_emisor not ilike '%juzgado%')