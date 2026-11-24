"""Standalone review workbook with text NPNs and full calculation provenance."""
from datetime import datetime
from zoneinfo import ZoneInfo
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill
from .core import visible_rows

ZONE_FIELDS=[('DIVIPOLA','municipality'),('Zona–sector (6–9)','zone_sector'),('Zona','zone_name'),('NPN únicos','npns'),('Prefijos de 13 dígitos','prefixes'),('Máximo bloque manzana (14–17)','max_m'),('NPN R1 de referencia','witness')]
PREFIX_FIELDS=[('DIVIPOLA','municipality'),('Zona–sector (6–9)','zone_sector'),('Prefijo territorial (1–13)','prefix13'),('NPN únicos','npns'),('Última manzana','max_m'),('Siguiente manzana (informativo)','next_m'),('NPN R1 de referencia','witness')]
BLOCK_FIELDS=[('DIVIPOLA','municipality'),('Zona–sector (6–9)','zone_sector'),('Prefijo territorial (1–13)','prefix13'),('Manzana completa (1–17)','block17'),('Manzana (14–17)','block'),('NPN únicos','npns'),('Códigos de terreno distintos','plots'),('Último terreno (18–21)','max_t'),('Siguiente terreno (informativo)','next_t'),('NPN R1 de referencia','witness')]


def export_maxima(filename,result,origin,catalog,municipality='',zone='',search=''):
    book=Workbook();summary=book.active;summary.title='Resumen'
    for row in [('Concepto','Valor'),('Fecha de consulta',datetime.now(ZoneInfo('America/Bogota')).isoformat(timespec='seconds')),('Origen R1',origin),('Alcance','Visualización de máximos; no se ejecuta ni se aprueba una renumeración.'),('Municipio filtrado',municipality or 'Todos'),('Zona–sector filtrado',zone or 'Todas'),('Búsqueda',search or 'Sin búsqueda'),('Registros leídos',result.source_rows),('NPN únicos válidos',result.unique_npns),('Duplicados excluidos',result.duplicates),('NPN vacíos',result.blanks),('NPN inválidos excluidos',len(result.invalid)),('SHA256 de NPN únicos',result.fingerprint),('Referencia manzana','Máximo calculado dentro del mismo prefijo de 13 dígitos. El resumen por zona–sector (6–9) es informativo.'),('Referencia terreno','Máximo calculado dentro de cada manzana completa de 17 dígitos.'),('Condiciones 8 y 9','No se validan reglas especiales. Se muestran los códigos existentes en el R1, sin aprobar renumeraciones.')]:summary.append(row)
    for title,fields,rows in [('Por zona-sector',ZONE_FIELDS,result.zones),('Por manzana',BLOCK_FIELDS,result.blocks)]:
        sheet=book.create_sheet(title);sheet.append(['Departamento','Municipio']+[label for label,_ in fields])
        for row in visible_rows(rows,municipality,zone,search,catalog):
            sheet.append(list(catalog.get(row['municipality'],('No identificado','No identificado')))+[row[key] for _,key in fields])
    invalid=book.create_sheet('Registros no utilizados');invalid.append(['Fila de origen','Valor NPN','Motivo'])
    for row in result.invalid:invalid.append(list(row))
    for sheet in book:
        sheet.freeze_panes='C2' if sheet.title.startswith('Por ') else 'B2';sheet.auto_filter.ref=sheet.dimensions
        for cell in sheet[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='0066B3')
        for column in sheet.columns:sheet.column_dimensions[column[0].column_letter].width=28
        for row in sheet:
            for cell in row:
                if isinstance(cell.value,str):cell.data_type='s'
    summary.column_dimensions['A'].width=38;summary.column_dimensions['B'].width=110
    book.save(filename)
