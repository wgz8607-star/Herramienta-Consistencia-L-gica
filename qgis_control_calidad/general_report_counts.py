"""Report display totals; published statements and reference rows remain intact."""
import re


def r1_total_rows(rows):
    matches=[]
    for row in rows:
        description=next((value for key,value in row.items() if str(key).casefold()=='descripcion'),'')
        if re.fullmatch(r'todos\s+los\s+registros\s+(?:de|del)\s+r1[.\s]*',str(description).strip(),re.I):
            matches.append(row)
    return matches


def apply_unique_filtered_r1_count(connection, rows, resolve_sql, check_cancelled=lambda: None):
    targets=r1_total_rows(rows)
    if not targets:
        return rows
    # resolve_sql points to the same filtered temporary R1 as the validation.
    query=resolve_sql("SELECT COUNT(DISTINCT NULLIF(btrim(numero_predial::text), '')) AS cantidad FROM {esquema_r1}.{tabla_r1}")
    check_cancelled()
    with connection.cursor() as cursor:
        cursor.execute(query)
        count=cursor.fetchone()[0]
    check_cancelled()
    for row in targets:
        key=next((key for key in row if str(key).casefold()=='cantidad'),'cantidad')
        row[key]=count
    return rows
