"""DT/operator exception controls shared by every record-level Excel report."""
from openpyxl.styles import PatternFill, Protection
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

HEADERS = ('Excepción DT', 'Observación DT', 'Excepción operador', 'Observación operador')
FIELDS = ('excepcion_dt', 'observacion_dt', 'excepcion_operador', 'observacion_operador')
DEFAULTS = ('No', '', 'No', '')


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
    """Require observation before Sí; grey and reject operator inputs when DT=Sí.

    XLSX cannot dynamically lock cells without macros. Stop validations enforce
    normal edits; import validates again because Excel paste can bypass them.
    """
    if last_row < first_row:
        return
    dt, note_dt, operator, note_operator = [get_column_letter(first_column + i) for i in range(4)]
    for offset, header in enumerate(HEADERS):
        sheet.cell(first_row - 1, first_column + offset).comment = Comment(
            'Complete primero la observación y luego escriba Sí. DT en Sí impide diligenciar los campos del operador. Los datos originales no se editan.', 'Validador')
    r = first_row
    visible = lambda cell: f'LEN(TRIM(CLEAN(SUBSTITUTE({cell},CHAR(160)," "))))>0'
    dt_rule = f'OR(${dt}{r}="No",AND(${dt}{r}="Sí",{visible(f"${note_dt}{r}")},${operator}{r}="No",${note_operator}{r}=""))'
    op_rule = f'IF(${dt}{r}="Sí",AND(${operator}{r}="No",${note_operator}{r}=""),OR(${operator}{r}="No",AND(${operator}{r}="Sí",{visible(f"${note_operator}{r}")})))'
    note_dt_rule = f'OR(${dt}{r}<>"Sí",{visible(f"${note_dt}{r}")})'
    note_op_rule = f'IF(${dt}{r}="Sí",${note_operator}{r}="",OR(${operator}{r}<>"Sí",{visible(f"${note_operator}{r}")}))'
    for column, formula in zip((dt, note_dt, operator, note_operator), (dt_rule, note_dt_rule, op_rule, note_op_rule)):
        validation = DataValidation(type='custom', formula1=formula, allow_blank=False)
        validation.showErrorMessage = True
        validation.errorStyle = 'stop'
        validation.errorTitle = 'Excepción no válida'
        validation.error = 'Diligencie la observación antes de marcar Sí. Si DT es Sí, el operador no puede registrar excepción ni observación.'
        validation.showInputMessage = True
        validation.promptTitle = 'Revisión de excepción'
        validation.prompt = 'Escriba Sí o No. Complete primero la observación. DT en Sí bloquea los campos del operador.'
        sheet.add_data_validation(validation)
        validation.add(f'{column}{first_row}:{column}{last_row}')
    sheet.conditional_formatting.add(
        f'{operator}{first_row}:{note_operator}{last_row}',
        FormulaRule(formula=[f'${dt}{first_row}="Sí"'], fill=PatternFill('solid', fgColor='D9D9D9')),
    )
    for row in sheet.iter_rows(min_row=first_row, max_row=last_row, min_col=first_column, max_col=first_column+3):
        for cell in row:
            cell.protection = Protection(locked=False)
    if protect:
        sheet.protection.sheet = True
        sheet.protection.autoFilter = False
        sheet.protection.selectLockedCells = False
        sheet.protection.selectUnlockedCells = False
