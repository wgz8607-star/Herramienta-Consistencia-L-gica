from contextlib import closing
import psycopg2

PROGRESS_METRICS = ('recognized_active', 'recognized_cancelled', 'quality_active', 'quality_cancelled',
                    'with_areas', 'snc', 'recognized_total', 'quality_total')


def progress_bundle(source, rows, metric_counts, areas_available, snc_available):
    indicators = []
    for (divipola, zone, code), counts in sorted(metric_counts.items()):
        data = dict(zip(PROGRESS_METRICS, counts))
        data.update(divipola=divipola, zona=zone, codigo_zona=code)
        if not areas_available: data['with_areas'] = None
        if not snc_available: data['snc'] = None
        indicators.append(data)
    return {'source': source, 'rows': rows, 'indicator_rows': indicators,
            'areas_available': areas_available, 'snc_available': snc_available}


def read_cica_stages(params, municipality="", include_source=False):
    """Compute the agreed indicators directly from cica_predio in one aggregate."""
    with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection, connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '60s'")
            cursor.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_schema=%s AND table_name=%s', ('snc_cica_copy', 'cica_predio'))
            fields = {row[0]: row[1] for row in cursor.fetchall()}
            area_field = next((name for name in ('area_geo_num', 'area_geografica') if name in fields), None)
            area_sql = 'NULL::numeric'
            if area_field:
                if fields[area_field] in ('smallint', 'integer', 'bigint', 'numeric', 'real', 'double precision'):
                    area_sql = area_field + '::numeric'
                else:
                    area_sql = "CASE WHEN replace(btrim(" + area_field + "::text), ',', '.') ~ '^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$' THEN replace(btrim(" + area_field + "::text), ',', '.')::numeric END"
            control_sql = 'estado_control::text' if 'estado_control' in fields else 'NULL::text'
            recognized = "etapa_original NOT IN ('SIN_ASIGNAR','PRE_ASIGNADO','ASIGNADO','PARA_DISPOSITIVO','EN_DISPOSITIVO')"
            quality = "etapa_original IN ('CONTROL_CALIDAD_GENERAL','CONTROL_CALIDAD_GRUPO','DEVUELTO','RECHAZADO','VALIDADO')"
            query = """WITH datos AS (
                SELECT substring(btrim(numero_predial::text), 1, 5) AS divipola,
                       substring(btrim(numero_predial::text), 6, 2) AS codigo_zona,
                       COALESCE(etapa::text, '') AS etapa, etapa::text AS etapa_original,
                       estado::text AS estado, {control_sql} AS estado_control, {area_sql} AS area_geo_num
                FROM snc_cica_copy.cica_predio
                {municipality_filter}
            ), zonas AS (
                SELECT *, CASE WHEN codigo_zona = '01' THEN 'Urbano'
                    WHEN codigo_zona = '00' THEN 'Rural'
                    WHEN codigo_zona ~ '^[0-9][0-9]$' AND codigo_zona > '01' THEN 'Centro poblado'
                    ELSE 'Sin alcance' END AS zona FROM datos
            ) SELECT divipola, zona, codigo_zona, etapa, count(*),
                count(*) FILTER (WHERE estado = 'ACTIVO'),
                count(*) FILTER (WHERE estado = 'CANCELADO'),
                count(*) FILTER (WHERE estado IS NULL OR estado NOT IN ('ACTIVO', 'CANCELADO')),
                count(*) FILTER (WHERE {recognized} AND estado = 'ACTIVO'),
                count(*) FILTER (WHERE {recognized} AND estado = 'CANCELADO'),
                count(*) FILTER (WHERE {quality} AND estado = 'ACTIVO'),
                count(*) FILTER (WHERE {quality} AND estado = 'CANCELADO'),
                count(*) FILTER (WHERE area_geo_num > 0 AND estado IS DISTINCT FROM 'CANCELADO'),
                count(*) FILTER (WHERE etapa_original = 'VALIDADO' AND estado_control = 'DESCARGADO_AL_SNC'),
                count(*) FILTER (WHERE {recognized}), count(*) FILTER (WHERE {quality})
            FROM zonas GROUP BY divipola, zona, codigo_zona, etapa
            ORDER BY divipola, CASE zona WHEN 'Urbano' THEN 1
                WHEN 'Centro poblado' THEN 2 WHEN 'Rural' THEN 3 ELSE 4 END,
                codigo_zona, etapa""".format(control_sql=control_sql, area_sql=area_sql, recognized=recognized, quality=quality,
                    municipality_filter='WHERE btrim(numero_predial::text) LIKE %s' if municipality else '')
            cursor.execute(query, (municipality + '%',) if municipality else ())
            raw_rows = cursor.fetchall()
            rows = [tuple(row[:8]) for row in raw_rows]
            metrics = {}
            for row in raw_rows:
                if len(row) < 16: continue
                values = metrics.setdefault(tuple(row[:3]), [0] * len(PROGRESS_METRICS))
                for index, count in enumerate(row[8:16]): values[index] += count
            data = progress_bundle('sentencias.snc_cica_copy.cica_predio', rows, metrics, bool(area_field), 'estado_control' in fields)
            return data if include_source else rows



def read_detail(params,municipality,selection='',cp='',offset=0):
    from .cica_zones import selected_zones
    zones=selected_zones(selection)
    conditions=['left(btrim(numero_predial::text),5)=%s'];args=[municipality]
    if zones is not None:
        clauses=[]
        for zone in zones:
            if zone=='Urbano':clauses.append("substring(btrim(numero_predial::text),6,2)='01'")
            elif zone=='Rural':clauses.append("substring(btrim(numero_predial::text),6,2)='00'")
            elif cp:
                clauses.append('substring(btrim(numero_predial::text),6,2)=%s');args.append(cp)
            else:clauses.append("substring(btrim(numero_predial::text),6,2) ~ '^(0[2-9]|[1-9][0-9])$'")
        conditions.append('('+' OR '.join(clauses)+')' if clauses else 'FALSE')
    with closing(psycopg2.connect(**params,connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection,connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='60s'")
            cursor.execute('SELECT numero_predial::text,etapa::text,estado::text,count(*) FROM snc_cica_copy.cica_predio WHERE '+' AND '.join(conditions)+' GROUP BY 1,2,3 ORDER BY 1,2,3 LIMIT 501 OFFSET %s',tuple(args+[offset]))
            rows=cursor.fetchall()
            return {'rows':rows[:500],'has_more':len(rows)>500}
