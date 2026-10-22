select cf.ilicode, lf.ente_emisor, lf.numero_fuente, lf.fecha_documento_fuente, lp.numero_predial, 'Fail' Cond_2_35
from {esquema}{punto}lc_fuenteadministrativa lf 
left join {esquema}{punto}col_fuenteadministrativatipo cf on cf.t_id = lf.tipo  
left join {esquema}{punto}col_unidadfuente cu on cu.fuente_administrativa = lf.t_id 
left join {esquema}{punto}lc_predio lp on lp.t_id = cu.unidad 
where (cf.ilicode  in ('Documento_Publico.Escritura_Publica', 'Documento_Publico.Sentencia_Judicial', 'Documento_Publico.Acto_Administrativo')
       and (lf.ente_emisor is null or lf.numero_fuente is null or lf.fecha_documento_fuente is null)) 
or (cf.ilicode  = 'Documento_Privado'
       and (lf.ente_emisor is not null or lf.numero_fuente is not null or lf.fecha_documento_fuente is null))
or (cf.ilicode  = 'Sin_Documento'
       and (lf.ente_emisor is not null or lf.numero_fuente is not null or lf.fecha_documento_fuente is not null))
