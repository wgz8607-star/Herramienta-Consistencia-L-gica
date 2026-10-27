"""DT/operator exception controls shared by every record-level Excel report."""
from copy import copy

from openpyxl.styles import PatternFill, Protection, Font
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

HEADERS = ('Excepción DT', 'Observación DT', 'Excepción operador', 'Observación operador')
FIELDS = ('excepcion_dt', 'observacion_dt', 'excepcion_operador', 'observacion_operador')
DEFAULTS = ('No', '', 'No', '')
EXCEPTION_COLORS = {'Sí': ('C6EFCE', '006100'), 'No': ('FFC7CE', '9C0006')}


def yes(value):
    return str(value or '').strip().casefold() in ('sí', 'si')


def validate(values, valid_observation):
    dt, note_dt, operator, note_operator = values
    if str(dt) not in ('Sí', 'No') or str(operator) not in ('Sí', 'No'):
        raise ValueError('Las excepciones deben marcarse como Sí o No.')
    if yes(dt) and not valid_observation(note_dt):
        raise ValueError('Excepción DT requiere una Observación DT válida.')
    if yes(dt) and (yes(operator) or str(note_operator or '')):
        raise ValueError('Si Excepción DT es Sí, los campos del operador deben quedar en No y vacíos.')
    if yes(operator) and not valid_observation(note_operator):
        raise ValueError('Excepción operador requiere una Observación operador válida.')


def add_controls(sheet, first_row, last_row, first_column, protect=True):
    """Sí/No dropdowns; DT=Sí visually hides only the operator cells."""
    if last_row < first_row:
        return
    dt, note_dt, operator, note_operator = [get_column_letter(first_column + i) for i in range(4)]
    for offset, header in enumerate(HEADERS):
        sheet.cell(first_row - 1, first_column + offset).comment = Comment(
            'Seleccione Sí o No. Las observaciones se pueden diligenciar antes o después. DT en Sí oculta visualmente solo los valores de las dos celdas del operador.', 'Validador')
    for column in (dt, operator):
        validation = DataValidation(type='list', formula1='"Sí,No"', allow_blank=False)
        validation.showDropDown = False
        validation.showErrorMessage = True
        validation.errorStyle = 'stop'
        validation.errorTitle = 'Valor fuera del dominio'
        validation.error = 'Seleccione Sí o No.'
        validation.showInputMessage = True
        validation.promptTitle = 'Excepción'
        validation.prompt = 'Seleccione Sí o No; la observación se diligencia libremente.'
        sheet.add_data_validation(validation)
        validation.add(f'{column}{first_row}:{column}{last_row}')
    sheet.conditional_formatting.add(
        f'{operator}{first_row}:{note_operator}{last_row}',
        FormulaRule(formula=[f'${dt}{first_row}="Sí"'],
                    fill=PatternFill('solid', fgColor='FFFFFF'),
                    font=Font(color='FFFFFF'), stopIfTrue=True),
    )
    for column in (dt, operator):
        for value, (color, text_color) in EXCEPTION_COLORS.items():
            sheet.conditional_formatting.add(
                f'{column}{first_row}:{column}{last_row}',
                FormulaRule(formula=[f'${column}{first_row}="{value}"'],
                            fill=PatternFill('solid', fgColor=color), font=Font(color=text_color)),
            )
    # Keep initial colors visible even in previews that do not calculate Excel
    # conditional formatting; conditional rules still update subsequent edits.
    for row_index in range(first_row, last_row + 1):
        for column_index in (first_column, first_column + 2):
            cell = sheet.cell(row_index, column_index)
            if cell.value in EXCEPTION_COLORS:
                fill_color, text_color = EXCEPTION_COLORS[cell.value]
                cell.fill = PatternFill('solid', fgColor=fill_color)
                font = copy(cell.font)
                font.color = text_color
                cell.font = font
    for row in sheet.iter_rows(min_row=first_row, max_row=last_row, min_col=first_column, max_col=first_column+3):
        for cell in row:
            cell.protection = Protection(locked=False)
    if protect:
        sheet.protection.sheet = True
        sheet.protection.autoFilter = False
        sheet.protection.selectLockedCells = False
        sheet.protection.selectUnlockedCells = False


def link_formula(sheet_name, key_column, first_row, last_row, role_column, summary_row):
    quoted = "'" + sheet_name.replace("'", "''") + "'"
    keys = f'{quoted}!${get_column_letter(key_column)}${first_row}:${get_column_letter(key_column)}${last_row}'
    values = f'{quoted}!${get_column_letter(role_column)}${first_row}:${get_column_letter(role_column)}${last_row}'
    return f'IF(COUNTIF({keys},$A{summary_row})=1,IFERROR(INDEX({values},MATCH($A{summary_row},{keys},0)),""),"")'


def link_rule_reviews(book):
    """Make detail rows editable and Revisión a key-based consolidated view."""
    summary = book['Revisión']
    origins = book.create_sheet('_OrigenRevision')
    origins.append(['hoja', 'columna_clave', 'primera_fila', 'ultima_fila', 'columna_excepcion'])
    lookup = {}
    for sheet in book:
        if sheet.title in ('Revisión', '_OrigenRevision') or sheet.max_row < 5:
            continue
        headers = {cell.value: cell.column for cell in sheet[4] if cell.value is not None}
        if 'clave_caso' not in headers or not all(name in headers for name in HEADERS):
            continue
        key_col, role_col = headers['clave_caso'], headers[HEADERS[0]]
        origins.append([sheet.title, key_col, 5, sheet.max_row, role_col])
        sheet.column_dimensions[get_column_letter(key_col)].hidden = True
        add_controls(sheet, 5, sheet.max_row, role_col)
        for row in range(5, sheet.max_row+1):
            key = sheet.cell(row, key_col).value
            lookup.setdefault(key, []).append((sheet.title, key_col, 5, sheet.max_row, role_col))
    origins.sheet_state = 'hidden'
    for row in range(2, summary.max_row+1):
        key = summary.cell(row, 1).value
        matches = lookup.get(key, [])
        if len(matches) != 1:
            continue
        name, key_col, first, last, role_col = matches[0]
        for offset in range(4):
            cell = summary.cell(row, 9+offset)
            cell.value = '=' + link_formula(name, key_col, first, last, role_col+offset, row)
            cell.protection = Protection(locked=True)
    # Detail editing is the sole source in a workbook with linked rule sheets.
    summary.data_validations.dataValidation = []
