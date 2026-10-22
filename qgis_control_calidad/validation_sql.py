RULES = {
1:("huecos_terreno_formal","Huecos en LC_Terreno formal"),2:("huecos_terreno_informal","Huecos en LC_Terreno informal"),
3:("huecos_manzana","Huecos en CC_Manzana"),4:("huecos_vereda","Huecos en CC_Vereda"),5:("huecos_sector_rural","Huecos en CC_SectorRural"),6:("huecos_sector_urbano","Huecos en CC_SectorUrbano"),7:("huecos_barrio","Huecos en CC_Barrio"),8:("huecos_localidad","Huecos en CC_LocalidadComuna"),9:("huecos_corregimiento","Huecos en CC_Corregimiento"),10:("huecos_centro_poblado","Huecos en CC_CentroPoblado"),11:("huecos_perimetro_urbano","Huecos en CC_PerimetroUrbano"),12:("huecos_limite_municipio","Huecos en CC_LimiteMunicipio"),13:("huecos_zhf_rural","Huecos en zona física rural"),14:("huecos_zhg_rural","Huecos en zona geoeconómica rural"),15:("huecos_zhf_urbana","Huecos en zona física urbana"),16:("huecos_zhg_urbana","Huecos en zona geoeconómica urbana"),
17:("superposicion_terreno_formal","Superposición entre terrenos formales"),18:("superposicion_terreno_informal","Superposición entre terrenos informales"),19:("superposicion_manzana","Superposición en CC_Manzana"),20:("posesion_informal_publico","Posesión informal sobre terreno público"),21:("ocupacion_informal_privado","Ocupación informal sobre terreno privado"),22:("superposicion_vereda","Superposición en CC_Vereda"),23:("superposicion_sector_rural","Superposición en CC_SectorRural"),24:("superposicion_sector_urbano","Superposición en CC_SectorUrbano"),25:("superposicion_barrio","Superposición en CC_Barrio"),26:("superposicion_localidad","Superposición en CC_LocalidadComuna"),27:("superposicion_corregimiento","Superposición en CC_Corregimiento"),28:("superposicion_centro_poblado","Superposición en CC_CentroPoblado"),29:("superposicion_perimetro_urbano","Superposición en CC_PerimetroUrbano"),30:("superposicion_limite_municipio","Superposición en CC_LimiteMunicipio"),31:("superposicion_unidad_formal_misma_planta","Unidades formales superpuestas con igual planta y tipo (posición 22 diferente de 2)"),32:("superposicion_unidad_informal_misma_planta","Unidades informales superpuestas con igual planta y tipo (posición 22 igual a 2)"),33:("coincidencia_extdireccion","Direcciones coincidentes"),34:("superposicion_zhf_rural","Superposición en zona física rural"),35:("superposicion_zhg_rural","Superposición en zona geoeconómica rural"),36:("superposicion_zhf_urbana","Superposición en zona física urbana"),37:("superposicion_zhg_urbana","Superposición en zona geoeconómica urbana"),
38:("contenencia_centro_limite","Centro poblado fuera de límite o corregimiento"),39:("contenencia_perimetro_limite","Perímetro urbano fuera de límite o corregimiento"),40:("contenencia_sector_urbano","Sector urbano fuera de centro poblado o perímetro"),41:("contenencia_sector_rural","Sector rural fuera de límite o corregimiento"),42:("contenencia_vereda_sector","Vereda fuera de sector rural"),43:("contenencia_localidad_sector","Localidad/comuna fuera de sector urbano"),44:("contenencia_barrio_localidad","Barrio fuera de localidad/comuna"),45:("contenencia_manzana_barrio","Manzana fuera de barrio"),46:("contenencia_direccion_terreno","Dirección fuera de su terreno"),47:("contenencia_unidad_formal","Unidad formal fuera de su terreno"),48:("contenencia_unidad_informal","Unidad informal fuera de su terreno"),49:("contenencia_terreno_zhg_urbana","Terreno urbano fuera de zona geoeconómica urbana"),50:("contenencia_terreno_zhf_urbana","Terreno urbano fuera de zona física urbana"),51:("contenencia_terreno_zhg_rural","Terreno rural fuera de zona geoeconómica rural"),52:("contenencia_terreno_zhf_rural","Terreno rural fuera de zona física rural"),53:("contenencia_informal_formal","Terreno informal no contenido por terreno formal"),
54:("cobertura_terreno_manzana","Cobertura mutua terreno urbano–manzana"),55:("cobertura_terreno_vereda","Cobertura mutua terreno rural–vereda"),56:("cobertura_zhg_zhf_rural","Cobertura mutua zonas rurales"),57:("cobertura_zhg_zhf_urbana","Cobertura mutua zonas urbanas"),
58:("atributos_perimetro_limite","Atributos de perímetro y límite municipal"),59:("atributos_centro_limite","Código de centro poblado y límite"),60:("atributos_sector_urbano_perimetro","Código de sector urbano y perímetro"),61:("atributos_sector_urbano_centro","Código de sector urbano y centro poblado"),62:("atributos_sector_rural","Código de sector rural y límite"),63:("atributos_localidad_sector","Código de localidad y sector urbano"),64:("atributos_barrio_localidad","Código de barrio y localidad"),65:("atributos_vereda_sector","Código de vereda y sector rural"),66:("atributos_manzana_barrio","Código de manzana y barrio"),67:("atributos_terreno_manzana","Código de terreno urbano y manzana"),68:("atributos_terreno_vereda","Código de terreno rural y vereda"),69:("atributos_construccion_terreno_no_ph","NPN de unidad y terreno formal no PH"),70:("atributos_construccion_terreno_ph","Primeros 22 dígitos del NPN de unidad y terreno PH"),71:("atributos_construccion_terreno_informal","NPN de unidad y terreno informal")}
LAYER_INFO = [(f"r{i:02d}_{RULES[i][0]}",f"{i:02d}",RULES[i][1]) for i in range(1,72)]
COMPLEMENTARY_LAYER_INFO = [
    ("c_i_unidad_formal_fuera", "I", "Parte de unidad formal no contenida en su terreno; PH usa el predio matriz"),
    ("c_ii_unidad_informal_fuera", "II", "Parte de unidad informal no contenida en su terreno informal"),
    ("c_iii_unidad_ph_fuera_matriz", "III", "Parte de unidad PH no contenida en el terreno de su predio matriz"),
    ("c_iv_intersecciones_terrenos", "IV", "Intersecciones pequeñas entre terrenos"),
    ("c_v_intersecciones_unidades", "V", "Intersecciones pequeñas entre unidades"),
    ("c_vi_intersecciones_terrenos_unidades", "VI", "Intersecciones pequeñas entre terrenos y unidades"),
    ("c_vii_unidades_misma_planta", "VII", "Unidades superpuestas con igual planta y tipo, sin clasificar el predio"),
    ("c_viii_predios_activos_sin_terreno", "VIII", "Predios activos diferentes de PH unidad predial sin polígono de CR_Terreno relacionado"),
    ("c_ix_terrenos_sin_predio", "IX", "Polígonos CR_Terreno sin predio relacionado"),
    ("c_x_unidades_sin_predio", "X", "Unidades de construcción sin predio relacionado"),
    ("c_xi_predios_sin_direccion", "XI", "Predios activos sin dirección espacial"),
    ("c_xii_direcciones_sin_predio", "XII", "Direcciones sin relación con predio"),
]

def build_steps(src,out,area_max,area_min,tolerance,selected):
    minimum=max(0.0,float(area_min)); tol=max(0.0,float(tolerance)); src='"'+src.replace('"','""')+'"'
    norm=lambda g: f"ST_SnapToGrid(ST_Force2D(ST_MakeValid({g})),{tol})" if tol else f"ST_Force2D(ST_MakeValid({g}))"
    name=lambda i:f"r{i:02d}_{RULES[i][0]}"
    schema_setup="" if out == "pg_temp" else f"CREATE SCHEMA {out};\n"
    prep=f"""{schema_setup}CREATE TABLE {out}._predio AS SELECT p.t_id,p.numero_predial,p.condicion_predio,p.tipo,
 substring(coalesce(p.numero_predial,''),22,1)<>'2' formal,
 substring(coalesce(p.numero_predial,''),22,1)='2' informal,
 EXISTS(SELECT 1 FROM {src}.lc_derecho d WHERE d.unidad=p.t_id AND d.tipo=747) posesion,
 EXISTS(SELECT 1 FROM {src}.lc_derecho d WHERE d.unidad=p.t_id AND d.tipo=746) ocupacion FROM {src}.lc_predio p;
CREATE TABLE {out}._terreno AS SELECT DISTINCT t.t_id,u.baunit predio_id,p.numero_predial,p.condicion_predio,p.tipo,p.formal,p.informal,p.posesion,p.ocupacion,({norm('t.geometria')})::geometry(Geometry,9377) geom FROM {src}.lc_terreno t JOIN {src}.col_uebaunit u ON u.ue_lc_terreno=t.t_id JOIN {out}._predio p ON p.t_id=u.baunit WHERE t.geometria IS NOT NULL;
CREATE TABLE {out}._construccion AS SELECT DISTINCT c.t_id,u.baunit predio_id,p.numero_predial,p.condicion_predio,p.formal,p.informal,({norm('c.geometria')})::geometry(Geometry,9377) geom FROM {src}.lc_construccion c JOIN {src}.col_uebaunit u ON u.ue_lc_construccion=c.t_id JOIN {out}._predio p ON p.t_id=u.baunit WHERE c.geometria IS NOT NULL;
CREATE TABLE {out}._unidad AS SELECT DISTINCT c.t_id,u.baunit predio_id,p.numero_predial,p.condicion_predio,p.formal,p.informal,c.planta_ubicacion,k.tipo_planta,({norm('c.geometria')})::geometry(Geometry,9377) geom FROM {src}.lc_unidadconstruccion c JOIN {src}.col_uebaunit u ON u.ue_lc_unidadconstruccion=c.t_id JOIN {out}._predio p ON p.t_id=u.baunit LEFT JOIN {src}.lc_caracteristicasunidadconstruccion k ON k.t_id=c.lc_caracteristicasunidadconstruccion WHERE c.geometria IS NOT NULL;
CREATE INDEX ON {out}._terreno USING gist(geom);CREATE INDEX ON {out}._construccion USING gist(geom);CREATE INDEX ON {out}._unidad USING gist(geom);"""
    steps=[("Preparando datos relacionados",prep)]; q={}
    def finish(i,body,geom="geometria"):
        n=name(i); q[n]=f"CREATE TABLE {out}.{n} AS {body}; ALTER TABLE {out}.{n} ADD PRIMARY KEY(fid); CREATE INDEX ON {out}.{n} USING gist({geom});"
    def holes(i,source,condition="true",obs="Revisar hueco topológico"):
        body=f"""WITH clase AS(SELECT ST_UnaryUnion(ST_Collect(geom))g FROM {source} WHERE {condition}),p AS(SELECT (ST_Dump(g)).geom g FROM clase WHERE g IS NOT NULL),h AS(SELECT ST_Difference(ST_MakePolygon(ST_ExteriorRing(g)),g)g FROM p),d AS(SELECT (ST_Dump(ST_CollectionExtract(ST_MakeValid(g),3))).geom g FROM h) SELECT row_number()over()::bigint fid,'{i:02d}'::text item,'{obs}'::text observacion,ST_Multi(g)::geometry(MultiPolygon,9377) geometria,round(ST_Area(g)::numeric,6)area_m2 FROM d WHERE NOT ST_IsEmpty(g) AND ST_Area(g)>{minimum}"""; finish(i,body)
    def terrain_holes(i,condition,obs):
        body=f"""WITH clase AS(SELECT ST_UnaryUnion(ST_Collect(geom))g FROM {out}._terreno WHERE {condition}),total AS(SELECT ST_UnaryUnion(ST_Collect(geom))g FROM {out}._terreno),p AS(SELECT (ST_Dump(g)).geom g FROM clase WHERE g IS NOT NULL),h AS(SELECT ST_Difference(ST_MakePolygon(ST_ExteriorRing(p.g)),p.g)g FROM p),libre AS(SELECT ST_Difference(h.g,total.g)g FROM h CROSS JOIN total),d AS(SELECT (ST_Dump(ST_CollectionExtract(ST_MakeValid(g),3))).geom g FROM libre)SELECT row_number()over()::bigint fid,'{i:02d}'::text item,'{obs}'::text observacion,ST_Multi(g)::geometry(MultiPolygon,9377)geometria,round(ST_Area(g)::numeric,6)area_m2 FROM d WHERE NOT ST_IsEmpty(g)AND ST_Area(g)>{minimum}""";finish(i,body)
    terrain_holes(1,"formal","Evaluar si corresponde a vías o cuerpos de agua");terrain_holes(2,"informal","Evaluar si corresponde a vías, cuerpos de agua o espacio no informal")
    class_tables={3:"cc_manzana",4:"cc_vereda",5:"cc_sectorrural",6:"cc_sectorurbano",7:"cc_barrio",8:"cc_localidadcomuna",9:"cc_corregimiento",10:"cc_centropoblado",11:"cc_perimetrourbano",12:"cc_limitemunicipio",13:"av_zonahomogeneafisicarural",14:"av_zonahomogeneageoeconomicarural",15:"av_zonahomogeneafisicaurbana",16:"av_zonahomogeneageoeconomicaurbana"}
    for i,t in class_tables.items(): holes(i,f"(SELECT {norm('geometria')} geom FROM {src}.{t} WHERE geometria IS NOT NULL)x")
    def overlap(i,source,condition="true",extra=""):
        body=f"""SELECT row_number()over()::bigint fid,'{i:02d}'::text item,a.t_id id_a,b.t_id id_b,{extra} ST_Multi(x.g)::geometry(MultiPolygon,9377) geometria,round(ST_Area(x.g)::numeric,6)area_m2 FROM {source} a JOIN {source} b ON a.t_id<b.t_id AND {condition} AND a.geom&&b.geom AND ST_Intersects(a.geom,b.geom) CROSS JOIN LATERAL(SELECT ST_CollectionExtract(ST_MakeValid(ST_Intersection(a.geom,b.geom)),3)g)x WHERE NOT ST_IsEmpty(x.g) AND ST_Area(x.g)>{minimum}""";finish(i,body)
    overlap(17,f"{out}._terreno","a.formal AND b.formal","a.numero_predial npn_a,b.numero_predial npn_b,"); overlap(18,f"{out}._terreno","a.informal AND b.informal","a.numero_predial npn_a,b.numero_predial npn_b,")
    def cross_terrain(i,left,right):
        body=f"""SELECT row_number()over()::bigint fid,'{i:02d}'::text item,a.t_id id_informal,b.t_id id_formal,a.numero_predial npn_informal,b.numero_predial npn_formal,ST_Multi(x.g)::geometry(MultiPolygon,9377)geometria,round(ST_Area(x.g)::numeric,6)area_m2 FROM {out}._terreno a JOIN {out}._terreno b ON {left} AND {right} AND a.geom&&b.geom AND ST_Intersects(a.geom,b.geom) CROSS JOIN LATERAL(SELECT ST_CollectionExtract(ST_MakeValid(ST_Intersection(a.geom,b.geom)),3)g)x WHERE NOT ST_IsEmpty(x.g) AND ST_Area(x.g)>{minimum}""";finish(i,body)
    cross_terrain(20,"a.informal AND a.posesion","b.formal AND b.tipo IN(729,730,731,732,733)");cross_terrain(21,"a.informal AND a.ocupacion","b.formal AND b.tipo=734")
    overlap_tables={19:"cc_manzana",22:"cc_vereda",23:"cc_sectorrural",24:"cc_sectorurbano",25:"cc_barrio",26:"cc_localidadcomuna",27:"cc_corregimiento",28:"cc_centropoblado",29:"cc_perimetrourbano",30:"cc_limitemunicipio",34:"av_zonahomogeneafisicarural",35:"av_zonahomogeneageoeconomicarural",36:"av_zonahomogeneafisicaurbana",37:"av_zonahomogeneageoeconomicaurbana"}
    for i,t in overlap_tables.items(): overlap(i,f"(SELECT t_id,{norm('geometria')} geom FROM {src}.{t} WHERE geometria IS NOT NULL)")
    same_floor="a.planta_ubicacion IS NOT DISTINCT FROM b.planta_ubicacion AND a.tipo_planta IS NOT DISTINCT FROM b.tipo_planta"
    unit_fields="a.numero_predial npn_a,b.numero_predial npn_b,a.planta_ubicacion planta_ubicacion_a,b.planta_ubicacion planta_ubicacion_b,a.tipo_planta tipo_planta_a,b.tipo_planta tipo_planta_b,"
    overlap(31,f"{out}._unidad",f"a.formal AND b.formal AND substring(coalesce(a.numero_predial,''),22,1)<>'2' AND substring(coalesce(b.numero_predial,''),22,1)<>'2' AND {same_floor}",unit_fields)
    overlap(32,f"{out}._unidad",f"a.informal AND b.informal AND substring(coalesce(a.numero_predial,''),22,1)='2' AND substring(coalesce(b.numero_predial,''),22,1)='2' AND {same_floor}",unit_fields)
    finish(33,f"""SELECT row_number()over()::bigint fid,'33'::text item,a.t_id id_a,b.t_id id_b,ST_Force2D(a.localizacion)::geometry(Point,9377) geometria,0::numeric area_m2 FROM {src}.extdireccion a JOIN {src}.extdireccion b ON a.t_id<b.t_id AND ST_Equals(a.localizacion,b.localizacion)""")
    def contain(i,child,parents):
        unions=" UNION ALL ".join(f"SELECT {norm('geometria')} g FROM {src}.{p} WHERE geometria IS NOT NULL" for p in parents)
        body=f"""WITH pg AS(SELECT ST_UnaryUnion(ST_Collect(g))g FROM({unions})z),c AS(SELECT t_id,{norm('geometria')}g FROM {src}.{child} WHERE geometria IS NOT NULL),e AS(SELECT c.t_id,CASE WHEN pg.g IS NULL THEN NULL ELSE ST_Difference(c.g,pg.g)END g FROM c CROSS JOIN pg),d AS(SELECT t_id,(ST_Dump(ST_CollectionExtract(ST_MakeValid(g),3))).geom g FROM e WHERE g IS NOT NULL) SELECT row_number()over()::bigint fid,'{i:02d}'::text item,t_id id_clase_1,ST_Multi(g)::geometry(MultiPolygon,9377)geometria,round(ST_Area(g)::numeric,6)area_m2 FROM d WHERE NOT ST_IsEmpty(g) AND ST_Area(g)>{minimum}""";finish(i,body)
    contain(38,"cc_centropoblado",["cc_limitemunicipio","cc_corregimiento"]);contain(39,"cc_perimetrourbano",["cc_limitemunicipio","cc_corregimiento"]);contain(40,"cc_sectorurbano",["cc_centropoblado","cc_perimetrourbano"]);contain(41,"cc_sectorrural",["cc_limitemunicipio","cc_corregimiento"]);contain(42,"cc_vereda",["cc_sectorrural"]);contain(43,"cc_localidadcomuna",["cc_sectorurbano"]);contain(44,"cc_barrio",["cc_localidadcomuna"]);contain(45,"cc_manzana",["cc_barrio"])
    finish(46,f"""WITH tg AS(SELECT predio_id,ST_UnaryUnion(ST_Collect(geom))g FROM {out}._terreno GROUP BY predio_id) SELECT row_number()over()::bigint fid,'46'::text item,d.t_id direccion_id,d.lc_predio_direccion predio_id,ST_Force2D(d.localizacion)::geometry(Point,9377)geometria,0::numeric area_m2 FROM {src}.extdireccion d LEFT JOIN tg ON tg.predio_id=d.lc_predio_direccion WHERE d.lc_predio_direccion IS NOT NULL AND (tg.g IS NULL OR NOT ST_CoveredBy(ST_Force2D(d.localizacion),tg.g))""")
    def own_out(i,source,flag):
        body=f"""WITH tg AS(SELECT predio_id,ST_UnaryUnion(ST_Collect(geom))g FROM {out}._terreno WHERE {flag} GROUP BY predio_id),e AS(SELECT c.*,CASE WHEN tg.g IS NULL THEN c.geom ELSE ST_Difference(c.geom,tg.g)END g FROM {source} c LEFT JOIN tg ON tg.predio_id=c.predio_id WHERE c.{flag}),d AS(SELECT e.*,(ST_Dump(ST_CollectionExtract(ST_MakeValid(g),3))).geom pieza FROM e) SELECT row_number()over()::bigint fid,'{i:02d}'::text item,t_id id_clase_1,predio_id,numero_predial,ST_Multi(pieza)::geometry(MultiPolygon,9377)geometria,round(ST_Area(pieza)::numeric,6)area_m2 FROM d WHERE NOT ST_IsEmpty(pieza) AND ST_Area(pieza)>{minimum}""";finish(i,body)
    own_out(47,f"{out}._unidad","formal");own_out(48,f"{out}._unidad","informal")
    def terrain_zone(i,table,condition):
        body=f"""WITH z AS(SELECT ST_UnaryUnion(ST_Collect({norm('geometria')}))g FROM {src}.{table}),e AS(SELECT t.t_id,t.numero_predial,CASE WHEN z.g IS NULL THEN t.geom ELSE ST_Difference(t.geom,z.g)END g FROM {out}._terreno t CROSS JOIN z WHERE {condition}),d AS(SELECT t_id,numero_predial,(ST_Dump(ST_CollectionExtract(ST_MakeValid(g),3))).geom g FROM e WHERE g IS NOT NULL)SELECT row_number()over()::bigint fid,'{i:02d}'::text item,t_id terreno_id,numero_predial,ST_Multi(g)::geometry(MultiPolygon,9377)geometria,round(ST_Area(g)::numeric,6)area_m2 FROM d WHERE NOT ST_IsEmpty(g)AND ST_Area(g)>{minimum}""";finish(i,body)
    terrain_zone(49,"av_zonahomogeneageoeconomicaurbana","substring(coalesce(t.numero_predial,''),6,2)<>'00'");terrain_zone(50,"av_zonahomogeneafisicaurbana","substring(coalesce(t.numero_predial,''),6,2)<>'00'");terrain_zone(51,"av_zonahomogeneageoeconomicarural","substring(coalesce(t.numero_predial,''),6,2)='00'");terrain_zone(52,"av_zonahomogeneafisicarural","substring(coalesce(t.numero_predial,''),6,2)='00'")
    finish(53,f"""WITH f AS(SELECT ST_UnaryUnion(ST_Collect(geom))g FROM {out}._terreno WHERE formal),e AS(SELECT t.t_id,t.numero_predial,CASE WHEN f.g IS NULL THEN t.geom ELSE ST_Difference(t.geom,f.g)END g FROM {out}._terreno t CROSS JOIN f WHERE t.informal),d AS(SELECT t_id,numero_predial,(ST_Dump(ST_CollectionExtract(ST_MakeValid(g),3))).geom g FROM e WHERE g IS NOT NULL)SELECT row_number()over()::bigint fid,'53'::text item,t_id terreno_id,numero_predial,ST_Multi(g)::geometry(MultiPolygon,9377) geometria,round(ST_Area(g)::numeric,6) area_m2 FROM d WHERE NOT ST_IsEmpty(g) AND ST_Area(g)>{minimum}""")
    def coverage(i,source_a,source_b,label_a,label_b):
        body=f"""WITH a AS(SELECT ST_UnaryUnion(ST_Collect(geom))g FROM {source_a}),b AS(SELECT ST_UnaryUnion(ST_Collect(geom))g FROM {source_b}),x AS(SELECT '{label_a}_no_cubierto_por_{label_b}'::text direccion,ST_Difference(a.g,b.g)g FROM a,b WHERE a.g IS NOT NULL AND b.g IS NOT NULL UNION ALL SELECT '{label_b}_no_cubierto_por_{label_a}',ST_Difference(b.g,a.g)FROM a,b WHERE a.g IS NOT NULL AND b.g IS NOT NULL),d AS(SELECT direccion,(ST_Dump(ST_CollectionExtract(ST_MakeValid(g),3))).geom g FROM x)SELECT row_number()over()::bigint fid,'{i:02d}'::text item,direccion,ST_Multi(g)::geometry(MultiPolygon,9377)geometria,round(ST_Area(g)::numeric,6)area_m2 FROM d WHERE NOT ST_IsEmpty(g)AND ST_Area(g)>{minimum}""";finish(i,body)
    srcgeom=lambda t:f"(SELECT {norm('geometria')} geom FROM {src}.{t} WHERE geometria IS NOT NULL)x"
    coverage(54,f"(SELECT geom FROM {out}._terreno WHERE substring(coalesce(numero_predial,''),6,2)<>'00')x",srcgeom("cc_manzana"),"terreno_urbano","manzana");coverage(55,f"(SELECT geom FROM {out}._terreno WHERE substring(coalesce(numero_predial,''),6,2)='00')x",srcgeom("cc_vereda"),"terreno_rural","vereda");coverage(56,srcgeom("av_zonahomogeneageoeconomicarural"),srcgeom("av_zonahomogeneafisicarural"),"zhg_rural","zhf_rural");coverage(57,srcgeom("av_zonahomogeneageoeconomicaurbana"),srcgeom("av_zonahomogeneafisicaurbana"),"zhg_urbana","zhf_urbana")
    def attr_pair(i,at,bt,mismatch,fields="NULL::text valor_1,NULL::text valor_2",sub="regla"):
        body=f"""SELECT row_number()over()::bigint fid,'{i:02d}'::text item,'{sub}'::text subregla,a.t_id id_clase_1,b.t_id id_clase_2,{fields},ST_Multi(x.g)::geometry(MultiPolygon,9377)geometria,round(ST_Area(x.g)::numeric,6)area_m2 FROM {src}.{at} a JOIN {src}.{bt} b ON a.geometria&&b.geometria AND ST_Intersects(a.geometria,b.geometria) CROSS JOIN LATERAL(SELECT ST_CollectionExtract(ST_MakeValid(ST_Intersection({norm('a.geometria')},{norm('b.geometria')})),3)g)x WHERE ({mismatch})AND NOT ST_IsEmpty(x.g)AND ST_Area(x.g)>{minimum}""";return body
    finish(58,attr_pair(58,"cc_perimetrourbano","cc_limitemunicipio","a.codigo_departamento IS DISTINCT FROM b.codigo_departamento OR a.codigo_municipio IS DISTINCT FROM b.codigo_municipio","a.codigo_municipio::text valor_1,b.codigo_municipio::text valor_2","departamento_municipio"))
    finish(59,attr_pair(59,"cc_centropoblado","cc_limitemunicipio","left(a.codigo,5) IS DISTINCT FROM coalesce(b.codigo_departamento,'')||right(coalesce(b.codigo_municipio,''),3)","a.codigo::text valor_1,(coalesce(b.codigo_departamento,'')||right(coalesce(b.codigo_municipio,''),3))::text valor_2","codigo"))
    finish(60,attr_pair(60,"cc_sectorurbano","cc_perimetrourbano","left(a.codigo,7) IS DISTINCT FROM coalesce(b.codigo_municipio,'')||coalesce(b.tipo_avaluo,'')","a.codigo::text valor_1,(coalesce(b.codigo_municipio,'')||coalesce(b.tipo_avaluo,''))::text valor_2","perimetro"))
    finish(61,attr_pair(61,"cc_sectorurbano","cc_centropoblado","left(a.codigo,7) IS DISTINCT FROM b.codigo","a.codigo::text valor_1,b.codigo::text valor_2","centro_poblado"))
    finish(62,attr_pair(62,"cc_sectorrural","cc_limitemunicipio","left(a.codigo,5) IS DISTINCT FROM coalesce(b.codigo_departamento,'')||right(coalesce(b.codigo_municipio,''),3)","a.codigo::text valor_1,(coalesce(b.codigo_departamento,'')||right(coalesce(b.codigo_municipio,''),3))::text valor_2","codigo"));finish(63,attr_pair(63,"cc_localidadcomuna","cc_sectorurbano","left(a.codigo,9) IS DISTINCT FROM b.codigo","a.codigo::text valor_1,b.codigo::text valor_2","codigo"));finish(64,attr_pair(64,"cc_barrio","cc_localidadcomuna","left(a.codigo,11) IS DISTINCT FROM b.codigo","a.codigo::text valor_1,b.codigo::text valor_2","codigo"));finish(65,attr_pair(65,"cc_vereda","cc_sectorrural","left(a.codigo,9) IS DISTINCT FROM b.codigo","a.codigo::text valor_1,b.codigo::text valor_2","codigo"));finish(66,attr_pair(66,"cc_manzana","cc_barrio","left(a.codigo,13) IS DISTINCT FROM b.codigo","a.codigo::text valor_1,b.codigo::text valor_2","codigo"))
    finish(67,attr_pair(67,"lc_terreno","cc_manzana","a.manzana_vereda_codigo IS DISTINCT FROM b.codigo","a.manzana_vereda_codigo::text valor_1,b.codigo::text valor_2","manzana"));finish(68,attr_pair(68,"lc_terreno","cc_vereda","a.manzana_vereda_codigo IS DISTINCT FROM b.codigo","a.manzana_vereda_codigo::text valor_1,b.codigo::text valor_2","vereda"))
    def pred_attr(i,where,mismatch):
        body=f"""SELECT row_number()over()::bigint fid,'{i:02d}'::text item,'npn'::text subregla,c.t_id id_clase_1,t.t_id id_clase_2,c.numero_predial::text valor_1,t.numero_predial::text valor_2,ST_Multi(x.g)::geometry(MultiPolygon,9377)geometria,round(ST_Area(x.g)::numeric,6)area_m2 FROM {out}._unidad c JOIN {out}._terreno t ON c.geom&&t.geom AND ST_Intersects(c.geom,t.geom) CROSS JOIN LATERAL(SELECT ST_CollectionExtract(ST_MakeValid(ST_Intersection(c.geom,t.geom)),3)g)x WHERE {where}AND({mismatch})AND NOT ST_IsEmpty(x.g)AND ST_Area(x.g)>{minimum}""";finish(i,body)
    pred_attr(69,"c.formal AND t.formal AND c.condicion_predio NOT IN(394,395) ","c.numero_predial IS DISTINCT FROM t.numero_predial");pred_attr(70,"c.formal AND t.formal AND c.condicion_predio IN(394,395) ","left(c.numero_predial,22) IS DISTINCT FROM left(t.numero_predial,22)");pred_attr(71,"c.informal AND t.informal ","c.numero_predial IS DISTINCT FROM t.numero_predial")
    for layer,code,_ in LAYER_INFO:
        if layer in selected: steps.append((f"Ejecutando ítem {code}",q[layer]))
    steps.append(("Finalizando",f"DROP TABLE {out}._unidad;DROP TABLE {out}._construccion;DROP TABLE {out}._terreno;DROP TABLE {out}._predio;"));return steps


# Adaptador para el Modelo Interno MAILC v1.0. La formulación original de las
# reglas usa nombres LC; esta capa traduce tablas, relaciones y dominios sin
# modificar nunca el esquema fuente.
_build_steps_lc = build_steps


def build_steps(src, out, area_max, area_min, tolerance, selected, minimum_width=0.0):
    source_schema = '"' + src.replace('"', '""') + '"'
    steps = _build_steps_lc(src, out, area_max, area_min, tolerance, selected)
    replacements = (
        ("lc_predio", "ilc_predio"),
        ("lc_derecho", "ilc_derecho"),
        ("lc_terreno", "cr_terreno"),
        ("ue_lc_terreno", "ue_cr_terreno"),
        ("lc_construccion", "cr_unidadconstruccion"),
        ("ue_lc_construccion", "ue_cr_unidadconstruccion"),
        ("lc_unidadconstruccion", "cr_unidadconstruccion"),
        ("ue_lc_unidadconstruccion", "ue_cr_unidadconstruccion"),
        ("lc_caracteristicasunidadconstruccion", "ilc_caracteristicasunidadconstruccion"),
        ("c.ilc_caracteristicasunidadconstruccion", "c.cr_caracteristicasunidadconstruccion"),
        ("c.planta_ubicacion,k.tipo_planta", "c.planta_ubicacion,c.tipo_planta"),
        ("lc_predio_direccion", "ilc_predio_direccion"),
        ("av_zonahomogenea", "vm_zonahomogenea"),
        ("numero_predial", "numero_predial_nacional"),
        ("d.tipo=745", "d.tipo=776"),
        ("d.tipo IN(746,747)", "d.tipo IN(777,778)"),
        ("d.tipo=747", "d.tipo=778"),
        ("d.tipo=746", "d.tipo=777"),
        ("p.condicion_predio<>401", "p.condicion_predio<>884"),
        ("p.condicion_predio=401", "p.condicion_predio=884"),
        ("b.tipo IN(729,730,731,732,733)", "b.tipo IN(1041,1042,1043,1044,1045)"),
        ("b.tipo=734", "b.tipo IN(1046,1047)"),
        ("c.condicion_predio NOT IN(394,395)", "c.condicion_predio NOT IN(877,878)"),
        ("c.condicion_predio IN(394,395)", "c.condicion_predio IN(877,878)"),
        ("iilc_predio_direccion", "ilc_predio_direccion"),
    )
    adapted = []
    for label, statement in steps:
        for old, new in replacements:
            statement = statement.replace(old, new)
        if label in {"Ejecutando ítem 67", "Ejecutando ítem 68"}:
            code = 67 if label.endswith("67") else 68
            table = "cc_manzana" if code == 67 else "cc_vereda"
            condition = "substring(coalesce(a.numero_predial_nacional,''),6,2)<>'00'" if code == 67 else "substring(coalesce(a.numero_predial_nacional,''),6,2)='00'"
            layer = RULES[code][0]
            statement = f"""CREATE TABLE {out}.r{code:02d}_{layer} AS
SELECT row_number() over()::bigint fid,'{code}'::text item,'codigo'::text subregla,
 a.t_id id_clase_1,b.t_id id_clase_2,left(a.numero_predial_nacional,17)::text valor_1,
 b.codigo::text valor_2,ST_Multi(x.g)::geometry(MultiPolygon,9377) geometria,
 round(ST_Area(x.g)::numeric,6) area_m2
FROM {out}._terreno a JOIN {source_schema}.{table} b
 ON a.geom&&b.geometria AND ST_Intersects(a.geom,b.geometria)
CROSS JOIN LATERAL(SELECT ST_CollectionExtract(ST_MakeValid(ST_Intersection(a.geom,ST_Force2D(ST_MakeValid(b.geometria)))),3)g)x
WHERE {condition} AND left(a.numero_predial_nacional,17) IS DISTINCT FROM b.codigo
 AND NOT ST_IsEmpty(x.g) AND ST_Area(x.g)>{max(0.0,float(area_min))};
ALTER TABLE {out}.r{code:02d}_{layer} ADD PRIMARY KEY(fid);
CREATE INDEX ON {out}.r{code:02d}_{layer} USING gist(geometria);"""
        adapted.append((label, statement))
    complementary_selected = {item[0] for item in COMPLEMENTARY_LAYER_INFO if item[0] in selected}
    if complementary_selected:
        maximum = max(float(area_max), float(area_min))
        minimum = max(0.0, float(area_min))
        width = max(0.0, float(minimum_width))
        width_filter = (
            f"AND (CASE WHEN ST_Perimeter(pieza)>0 THEN 2*ST_Area(pieza)/ST_Perimeter(pieza) ELSE 0 END)>={width}"
        )
        sql_by_layer = {}
        def containment(layer, code, condition, parent_join, observation, unit_condition):
            sql_by_layer[layer] = f"""CREATE TABLE {out}.{layer} AS
WITH padres AS (SELECT {parent_join} predio_id,ST_UnaryUnion(ST_Collect(t.geom)) geom FROM {out}._terreno t GROUP BY {parent_join}),
dif AS (SELECT u.*,CASE WHEN p.geom IS NULL THEN u.geom ELSE ST_Difference(u.geom,p.geom) END diferencia FROM {out}._unidad u LEFT JOIN padres p ON {condition} WHERE {unit_condition}),
piezas AS (SELECT d.*,(ST_Dump(ST_CollectionExtract(ST_MakeValid(diferencia),3))).geom pieza FROM dif d WHERE diferencia IS NOT NULL)
SELECT row_number() over()::bigint fid,'{code}'::text item,t_id unidad_id,predio_id,numero_predial_nacional,planta_ubicacion,tipo_planta,
CASE WHEN coalesce(planta_ubicacion,1)>1 THEN 'Posible volado al ser superior a planta 1' ELSE '{observation}' END::text observacion,
ST_Multi(pieza)::geometry(MultiPolygon,9377) geometria,round(ST_Area(pieza)::numeric,6) area_m2,
round(ST_Perimeter(pieza)::numeric,6) perimetro_m,round((CASE WHEN ST_Perimeter(pieza)>0 THEN 2*ST_Area(pieza)/ST_Perimeter(pieza) ELSE 0 END)::numeric,9) ancho_equiv_m
FROM piezas WHERE NOT ST_IsEmpty(pieza) AND ST_Area(pieza)>={minimum} {width_filter};
ALTER TABLE {out}.{layer} ADD PRIMARY KEY(fid);CREATE INDEX ON {out}.{layer} USING gist(geometria);"""
        containment("c_i_unidad_formal_fuera", "I", "p.predio_id=u.predio_id", "t.predio_id", "Unidad formal fuera de su terreno", "u.formal AND substring(coalesce(u.numero_predial_nacional,''),22,1)<>'9'")
        containment("c_ii_unidad_informal_fuera", "II", "p.predio_id=u.predio_id", "t.predio_id", "Unidad informal fuera de su terreno", "u.informal")
        sql_by_layer["c_iii_unidad_ph_fuera_matriz"] = f"""CREATE TABLE {out}.c_iii_unidad_ph_fuera_matriz AS
WITH padres AS (SELECT left(numero_predial_nacional,22) raiz,ST_UnaryUnion(ST_Collect(geom)) geom FROM {out}._terreno WHERE substring(coalesce(numero_predial_nacional,''),22,1)='9' AND substring(coalesce(numero_predial_nacional,''),23,8)='00000000' GROUP BY left(numero_predial_nacional,22)),
dif AS (SELECT u.*,CASE WHEN p.geom IS NULL THEN u.geom ELSE ST_Difference(u.geom,p.geom) END diferencia FROM {out}._unidad u LEFT JOIN padres p ON p.raiz=left(u.numero_predial_nacional,22) WHERE substring(coalesce(u.numero_predial_nacional,''),22,1)='9'),
piezas AS (SELECT d.*,(ST_Dump(ST_CollectionExtract(ST_MakeValid(diferencia),3))).geom pieza FROM dif d WHERE diferencia IS NOT NULL)
SELECT row_number()over()::bigint fid,'III'::text item,t_id unidad_id,predio_id,numero_predial_nacional,planta_ubicacion,tipo_planta,
CASE WHEN coalesce(planta_ubicacion,1)>1 THEN 'Posible volado al ser superior a planta 1' ELSE 'Unidad PH fuera del predio matriz' END::text observacion,
ST_Multi(pieza)::geometry(MultiPolygon,9377) geometria,round(ST_Area(pieza)::numeric,6) area_m2,round(ST_Perimeter(pieza)::numeric,6) perimetro_m,
round((CASE WHEN ST_Perimeter(pieza)>0 THEN 2*ST_Area(pieza)/ST_Perimeter(pieza) ELSE 0 END)::numeric,9) ancho_equiv_m
FROM piezas WHERE NOT ST_IsEmpty(pieza) AND ST_Area(pieza)>={minimum} {width_filter};ALTER TABLE {out}.c_iii_unidad_ph_fuera_matriz ADD PRIMARY KEY(fid);CREATE INDEX ON {out}.c_iii_unidad_ph_fuera_matriz USING gist(geometria);"""
        def intersections(layer, code, source_a, source_b, join_condition):
            sql_by_layer[layer] = f"""CREATE TABLE {out}.{layer} AS SELECT row_number()over()::bigint fid,'{code}'::text item,a.t_id id_a,b.t_id id_b,
ST_Multi(x.pieza)::geometry(MultiPolygon,9377) geometria,round(ST_Area(x.pieza)::numeric,6) area_m2,round(ST_Perimeter(x.pieza)::numeric,6) perimetro_m,
round((CASE WHEN ST_Perimeter(x.pieza)>0 THEN 2*ST_Area(x.pieza)/ST_Perimeter(x.pieza) ELSE 0 END)::numeric,9) ancho_equiv_m
FROM {source_a} a JOIN {source_b} b ON {join_condition} AND a.geom&&b.geom AND ST_Intersects(a.geom,b.geom)
CROSS JOIN LATERAL (SELECT (ST_Dump(ST_CollectionExtract(ST_MakeValid(ST_Intersection(a.geom,b.geom)),3))).geom pieza)x
WHERE NOT ST_IsEmpty(x.pieza) AND ST_Area(x.pieza)>={minimum} AND ST_Area(x.pieza)<={maximum} {width_filter.replace('pieza','x.pieza')};
ALTER TABLE {out}.{layer} ADD PRIMARY KEY(fid);CREATE INDEX ON {out}.{layer} USING gist(geometria);"""
        intersections("c_iv_intersecciones_terrenos", "IV", f"{out}._terreno", f"{out}._terreno", "a.t_id<b.t_id")
        intersections("c_v_intersecciones_unidades", "V", f"{out}._unidad", f"{out}._unidad", "a.t_id<b.t_id")
        intersections("c_vi_intersecciones_terrenos_unidades", "VI", f"{out}._terreno", f"{out}._unidad", "true")
        sql_by_layer["c_vii_unidades_misma_planta"] = f"""CREATE TABLE {out}.c_vii_unidades_misma_planta AS
SELECT row_number()over()::bigint fid,'VII'::text item,a.t_id id_a,b.t_id id_b,
a.numero_predial_nacional npn_a,b.numero_predial_nacional npn_b,
a.planta_ubicacion planta_ubicacion_a,b.planta_ubicacion planta_ubicacion_b,
a.tipo_planta tipo_planta_a,b.tipo_planta tipo_planta_b,
ST_Multi(x.pieza)::geometry(MultiPolygon,9377) geometria,
round(ST_Area(x.pieza)::numeric,6) area_m2,round(ST_Perimeter(x.pieza)::numeric,6) perimetro_m,
round((CASE WHEN ST_Perimeter(x.pieza)>0 THEN 2*ST_Area(x.pieza)/ST_Perimeter(x.pieza) ELSE 0 END)::numeric,9) ancho_equiv_m
FROM {out}._unidad a JOIN {out}._unidad b ON a.t_id<b.t_id
 AND a.planta_ubicacion IS NOT DISTINCT FROM b.planta_ubicacion
 AND a.tipo_planta IS NOT DISTINCT FROM b.tipo_planta
 AND a.geom&&b.geom AND ST_Intersects(a.geom,b.geom)
CROSS JOIN LATERAL (SELECT (ST_Dump(ST_CollectionExtract(ST_MakeValid(ST_Intersection(a.geom,b.geom)),3))).geom pieza)x
WHERE NOT ST_IsEmpty(x.pieza) AND ST_Area(x.pieza)>={minimum} {width_filter.replace('pieza','x.pieza')};
ALTER TABLE {out}.c_vii_unidades_misma_planta ADD PRIMARY KEY(fid);
CREATE INDEX ON {out}.c_vii_unidades_misma_planta USING gist(geometria);"""
        sql_by_layer["c_viii_predios_activos_sin_terreno"] = f"""CREATE TABLE {out}.c_viii_predios_activos_sin_terreno AS
SELECT row_number()over()::bigint fid,'VIII'::text item,p.t_id predio_id,p.numero_predial_nacional,
cp.ilicode condicion_predio,'Predio activo diferente de PH unidad predial sin polígono de CR_Terreno relacionado'::text observacion,
NULL::geometry(Geometry,9377) geometria
FROM {source_schema}.ilc_predio p
LEFT JOIN {source_schema}.ilc_condicionprediotipo cp ON cp.t_id=p.condicion_predio
WHERE p.fin_vida_util_version IS NULL
 AND coalesce(cp.ilicode,'')<>'PH.Unidad_Predial'
 AND NOT EXISTS(SELECT 1 FROM {source_schema}.col_uebaunit r JOIN {source_schema}.cr_terreno t ON t.t_id=r.ue_cr_terreno
                WHERE r.baunit=p.t_id AND t.geometria IS NOT NULL);
ALTER TABLE {out}.c_viii_predios_activos_sin_terreno ADD PRIMARY KEY(fid);"""
        sql_by_layer["c_ix_terrenos_sin_predio"] = f"""CREATE TABLE {out}.c_ix_terrenos_sin_predio AS
SELECT row_number()over()::bigint fid,'IX'::text item,t.t_id terreno_id,t.local_id,
'Polígono CR_Terreno sin predio relacionado'::text observacion,
ST_Multi(ST_CollectionExtract(ST_Force2D(ST_MakeValid(t.geometria)),3))::geometry(MultiPolygon,9377) geometria,
round(ST_Area(ST_Force2D(ST_MakeValid(t.geometria)))::numeric,6) area_m2
FROM {source_schema}.cr_terreno t
WHERE t.geometria IS NOT NULL
 AND NOT EXISTS(SELECT 1 FROM {source_schema}.col_uebaunit r JOIN {source_schema}.ilc_predio p ON p.t_id=r.baunit
                WHERE r.ue_cr_terreno=t.t_id);
ALTER TABLE {out}.c_ix_terrenos_sin_predio ADD PRIMARY KEY(fid);
CREATE INDEX ON {out}.c_ix_terrenos_sin_predio USING gist(geometria);"""
        sql_by_layer["c_x_unidades_sin_predio"] = f"""CREATE TABLE {out}.c_x_unidades_sin_predio AS
SELECT row_number()over()::bigint fid,'X'::text item,u.t_id unidad_id,u.local_id,u.planta_ubicacion,u.tipo_planta,
'Unidad de construcción sin predio relacionado'::text observacion,
ST_Multi(ST_CollectionExtract(ST_Force2D(ST_MakeValid(u.geometria)),3))::geometry(MultiPolygon,9377) geometria,
round(ST_Area(ST_Force2D(ST_MakeValid(u.geometria)))::numeric,6) area_m2
FROM {source_schema}.cr_unidadconstruccion u
WHERE u.geometria IS NOT NULL
 AND NOT EXISTS(SELECT 1 FROM {source_schema}.col_uebaunit r JOIN {source_schema}.ilc_predio p ON p.t_id=r.baunit
                WHERE r.ue_cr_unidadconstruccion=u.t_id);
ALTER TABLE {out}.c_x_unidades_sin_predio ADD PRIMARY KEY(fid);
CREATE INDEX ON {out}.c_x_unidades_sin_predio USING gist(geometria);"""
        sql_by_layer["c_xi_predios_sin_direccion"] = f"""CREATE TABLE {out}.c_xi_predios_sin_direccion AS
SELECT row_number()over()::bigint fid,'XI'::text item,p.t_id predio_id,p.numero_predial_nacional,
cp.ilicode condicion_predio,'Predio activo sin dirección espacial'::text observacion,
NULL::geometry(Geometry,9377) geometria
FROM {source_schema}.ilc_predio p
LEFT JOIN {source_schema}.ilc_condicionprediotipo cp ON cp.t_id=p.condicion_predio
WHERE p.fin_vida_util_version IS NULL
 AND NOT EXISTS(SELECT 1 FROM {source_schema}.extdireccion d
                WHERE d.ilc_predio_direccion=p.t_id AND d.localizacion IS NOT NULL);
ALTER TABLE {out}.c_xi_predios_sin_direccion ADD PRIMARY KEY(fid);"""
        sql_by_layer["c_xii_direcciones_sin_predio"] = f"""CREATE TABLE {out}.c_xii_direcciones_sin_predio AS
SELECT row_number()over()::bigint fid,'XII'::text item,d.t_id direccion_id,d.ilc_predio_direccion predio_id,
d.es_direccion_principal,d.nombre_predio,'Dirección sin relación con predio'::text observacion,
CASE WHEN d.localizacion IS NULL THEN NULL ELSE ST_Force2D(d.localizacion)::geometry(Geometry,9377) END geometria
FROM {source_schema}.extdireccion d
LEFT JOIN {source_schema}.ilc_predio p ON p.t_id=d.ilc_predio_direccion
WHERE d.ilc_predio_direccion IS NULL OR p.t_id IS NULL;
ALTER TABLE {out}.c_xii_direcciones_sin_predio ADD PRIMARY KEY(fid);
CREATE INDEX ON {out}.c_xii_direcciones_sin_predio USING gist(geometria);"""
        final_index = next((index for index, (label, _sql) in enumerate(adapted) if label == "Finalizando"), len(adapted))
        for layer, code, _description in COMPLEMENTARY_LAYER_INFO:
            if layer in complementary_selected:
                adapted.insert(final_index, (f"Ejecutando complemento {code}", sql_by_layer[layer]))
                final_index += 1
    return adapted
