with base as( --tabla base en la cual se alistan todas las novedades
	select 
		'{esquema}' mun,-- nombre el municipio 
		lp.t_id tid_predio, 
		lp.numero_predial npn_predio,
		lp.tiene_fmi,
		lp.matricula_inmobiliaria, 
		/*ld.t_id tid_datos_adic,
		le.t_id tid_novedad,
		le.tipo_novedad,*/
		le.numero_predial npn_novedad,
		letn.itfcode cod_novedad,
		letn.ilicode novedad
	from {esquema}.lc_predio lp 
	full outer join {esquema}.lc_datosadicionaleslevantamientocatastral ld on ld.lc_predio =lp.t_id 
	full outer join {esquema}.lc_estructuranovedadnumeropredial le  on le.lc_dtsdcnlstmntctstral_novedad_numeros_prediales =ld.t_id 
	full outer join {esquema}.lc_estructuranovedadnumeropredial_tipo_novedad letn on le.tipo_novedad =letn.t_id
)
, englobe as( --se aislan los predios que tengan asociada novedad de englobe
	select 
		* 
	from base 
	where novedad ='Englobe'
)
,tb_base_englobes as(--se filtra la tabla base para q solo traiga numeros prediales de lc_predio que esten asociados a un englobe, ya sea en lc_predio o en lc_estructuranovedadnumeropredial
	select 
		*  
	from base 
	where 1=1
		and (npn_predio in (select npn_predio from englobe) 
		or  npn_predio in (select npn_novedad from englobe))
	order by npn_novedad, novedad
)
,r_1 as(
	select
		 e1.mun
		,e1.tid_predio
		,e1.npn_predio
		,e1.tiene_fmi
		,e1.matricula_inmobiliaria
		,e1.npn_novedad
		,e1.cod_novedad c_n
		,e1.novedad
		,e2.npn_novedad  npn_novedad2
		,e2.cod_novedad c_n2
		,e2.novedad novedad2
		,count(e1.npn_predio) over (partition by e1.npn_predio) conteo_grupo
	from tb_base_englobes e1 
	left join tb_base_englobes e2 on e1.npn_novedad=e2.npn_predio
	where e1.cod_novedad =2
	order by npn_predio
)
,validacion_inicial as(
	select 
	* 
	,case when conteo_grupo <2 then 'Fail' else 'OK' end as validacion_numerica
	,case when 'Englobe' in     (select novedad2 from r_1 r_1_ where r_1.npn_novedad=r_1_.npn_novedad) then 'P_MT'--PREDIO CONSERVA NUMERO PREDIAL (MANTIENE EL TERRENO)
		  when 'Englobe' not in (select novedad2 from r_1 r_1_ where r_1.npn_novedad=r_1_.npn_novedad) then 'P_RN'--PREDIO NUEVO (RESULTANTE NUEVO)
		  else 'Fail' end as validador_posible_caso
	,case when r_1.novedad2 is null 
		    or r_1.novedad2 not in ('Cancelacion','Englobe')
			then 'Fail'    else 'OK' end as validador_posibles_novedades
	,case when r_1.novedad2 = 'Cancelacion' 
		   and r_1.npn_novedad=r_1.npn_novedad2 
		  then 'OK'
		  when r_1.novedad = 'Englobe' 
		   and r_1.npn_predio = r_1.npn_novedad 
		   and r_1.npn_novedad2=r_1.npn_novedad 
		  then 'OK'
		  else 'Fail'
		  end as validador_coherencia
	from r_1  
	order by npn_predio
)
,tb_final as(
	select
		vi.mun
		,vi.tid_predio
		,rdcr.numero_predial 
		,vi.npn_predio
		,vi.tiene_fmi
		,vi.matricula_inmobiliaria
		,vi.npn_novedad
		,vi.novedad
		,vi.npn_novedad2
		,vi.novedad2
		,case when vi.matricula_inmobiliaria is not null then 'OK' else 'Fail' end as CONDICION_8
		,case when rdcr.numero_predial is null then 'Fail' else 'OK' end as CONDICION_9
		,case when substring(vi.npn_novedad,22,1)='2' then 'Fail' else 'OK' end as CONDICION_10
		,case when substring(vi.npn_novedad,18,1) in ('9','A','B','C','D','E') then 'Fail' else 'OK' end as CONDICION_11
		,case when substring(vi.npn_predio ,22,1)='2' then 'Fail' else 'OK' end as CONDICION_12
		,case when vi.validador_posible_caso='P_RN' 
			   and substring (vi.npn_predio ,18,1) in ('9','A','B','C')  then 'OK' 
			  when vi.validador_posible_caso <> 'P_RN' then 'OK'
			   else 'Fail' end as CONDICION_14
		,case when vi.validacion_numerica ='OK' 
			   and vi.validador_posible_caso<>'Fail' 
			   and vi.validador_posibles_novedades ='OK'
			   and vi.validador_coherencia ='OK'
			  then vi.validador_posible_caso else 'Fail' end as CONDICION_13_15 --VALIDA LAS CONDICIONES DE COHERENCIA PARA LOS POSIBLES CASOS DE ENGLOBES 
	from validacion_inicial vi
	left join {esquema_r1}.{tabla_r1}  rdcr on rdcr.numero_predial = VI.npn_novedad
)
select * from tb_final
where 1=1
and (CONDICION_13_15='Fail' or CONDICION_8<>'OK' or CONDICION_9<>'OK' or CONDICION_10<>'OK' or CONDICION_11<>'OK' or CONDICION_12<>'OK' or CONDICION_14<>'OK')
order by npn_predio
