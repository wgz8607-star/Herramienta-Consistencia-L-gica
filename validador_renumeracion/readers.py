"""Read-only R1 inputs. Numeric Excel NPNs are reported rather than guessed."""
import csv
from pathlib import Path
import re
import unicodedata
from openpyxl import load_workbook

NPN_NAMES=('numero_predial','numero_predial_nacional','numeropredial','no_predial','nopredial')


def normalized(value):
    value=unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode().lower()
    return re.sub('[^a-z0-9]+','_',value).strip('_')


def inspect_excel(filename,sheet=None):
    book=load_workbook(filename,read_only=True,data_only=True)
    try:
        names=book.sheetnames
        selected=sheet or next((name for name in names if name.casefold()=='r1'),names[0])
        worksheet=book[selected]
        worksheet.reset_dimensions()
        for number,row in enumerate(worksheet.iter_rows(max_row=50,values_only=True),1):
            headers=[str(value or '') for value in row]
            candidates=[index for index,value in enumerate(headers) if normalized(value) in NPN_NAMES]
            if candidates:
                return names,selected,number,headers,min(candidates,key=lambda index:NPN_NAMES.index(normalized(headers[index])))
        raise ValueError('No se encontró un encabezado de número predial en las primeras 50 filas de esta hoja.')
    finally:book.close()


def file_records(filename,sheet='',header_row=1,column=0):
    path=Path(filename)
    if path.suffix.lower()=='.xlsx':
        book=load_workbook(path,read_only=True,data_only=True)
        try:
            worksheet=book[sheet or book.sheetnames[0]];worksheet.reset_dimensions()
            for number,row in enumerate(worksheet.iter_rows(min_row=header_row+1,max_col=column+1,values_only=True),header_row+1):
                yield number,row[column] if column<len(row) else None
        finally:book.close()
    elif path.suffix.lower()=='.txt':
        encoding='utf-8-sig'
        try:
            with path.open(encoding=encoding) as stream:
                for _ in stream:pass
        except UnicodeDecodeError:encoding='cp1252'
        with path.open(encoding=encoding,newline='') as stream:
            for number,line in enumerate(stream,1):
                line=line.rstrip('\r\n')
                if not line.strip():yield number,None;continue
                if len(line)!=312 or line[30]!='1':
                    raise ValueError(f'Línea {number}: el TXT R1 debe tener 312 caracteres y tipo de registro 1 en la posición 31.')
                yield number,line[:30]
    else:raise ValueError('Seleccione un R1 Excel (.xlsx) o TXT estándar (.txt).')


def municipality_catalog(filename):
    book=load_workbook(filename,read_only=True,data_only=True)
    try:
        return {str(code).strip().zfill(5):(str(department).strip(),str(municipality).strip()) for code,department,municipality in book.active.iter_rows(min_row=2,max_col=3,values_only=True) if code is not None and department is not None and municipality is not None}
    finally:book.close()
