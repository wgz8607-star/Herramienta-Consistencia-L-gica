import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpyxl import load_workbook
from qgis_control_calidad.review import build_cases, digest, load_review, restore_review, save_review
from qgis_control_calidad.report_exceptions import HEADERS, FIELDS, DEFAULTS


def cases():
    rule = SimpleNamespace(category='Administrativas', rule='r1', status='Correcta',
                           criterion_hash=digest('SELECT validacion'), identity_safe=True,
                           rows=[{'numero_predial': '00001', 'dato': 'valor'}])
    return build_cases([rule], {'model': 'CICA', 'schema': 'test'})


class ReportExceptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'review.xlsx'

    def test_dt_and_operator_require_their_own_observation(self):
        for field, note in (('excepcion_dt', 'observacion_dt'), ('excepcion_operador', 'observacion_operador')):
            row = cases()[0]
            setattr(row, field, 'Sí')
            for value in ('', '  ', '\u200b'):
                setattr(row, note, value)
                with self.assertRaises(ValueError):
                    save_review(self.path, [row])
            setattr(row, note, 'Justificación válida')
            save_review(self.path, [row])

    def test_dt_disallows_operator_fields_even_if_operator_is_not_exception(self):
        row = cases()[0]
        row.excepcion_dt = 'Sí'; row.observacion_dt = 'Validado DT'
        for flag, note in (('Sí', 'Observación operador'), ('No', 'Texto residual')):
            row.excepcion_operador, row.observacion_operador = flag, note
            with self.assertRaises(ValueError):
                save_review(self.path, [row])

    def test_export_fields_validation_protection_and_gray_operator(self):
        save_review(self.path, cases())
        book = load_workbook(self.path); sheet = book['Revisión']
        self.assertEqual(tuple(sheet.cell(1, col).value for col in range(9, 13)), HEADERS)
        self.assertEqual(tuple(sheet.cell(2, col).value or '' for col in range(9, 13)), DEFAULTS)
        self.assertTrue(sheet.protection.sheet)
        self.assertTrue(sheet['A2'].protection.locked)
        for col in ('I', 'J', 'K', 'L'):
            self.assertFalse(sheet[f'{col}2'].protection.locked)
        validations = list(sheet.data_validations.dataValidation)
        self.assertEqual(len(validations), 4)
        for rule in validations:
            self.assertEqual(rule.errorStyle, 'stop')
            self.assertTrue(rule.showErrorMessage)
            self.assertLessEqual(len(rule.formula1), 255)
        self.assertIn('$I2="Sí"', validations[2].formula1)
        self.assertIn('$L2=""', validations[2].formula1)
        self.assertGreater(len(sheet.conditional_formatting), 0)
        book.close()

    def test_yes_green_no_red_and_dt_operator_gray_has_priority(self):
        save_review(self.path, cases())
        book = load_workbook(self.path); sheet = book['Revisión']
        rules = [(str(area.sqref), rule) for area in sheet.conditional_formatting
                 for rule in sheet.conditional_formatting[area]]
        flags = [rule for area, rule in rules if area == 'I2']
        self.assertEqual({tuple(rule.formula): rule.dxf.fill.fgColor.rgb for rule in flags},
                         {('$I2="Sí"',): '00C6EFCE', ('$I2="No"',): '00FFC7CE'})
        gray = next(rule for area, rule in rules if area == 'K2:L2')
        self.assertTrue(gray.stopIfTrue)
        self.assertEqual(gray.dxf.fill.fgColor.rgb, '00D9D9D9')
        self.assertLess(gray.priority, min(rule.priority for area, rule in rules if area == 'K2'))
        book.close()

    def test_recovery_preserves_dt_or_operator_only_when_case_unchanged(self):
        for flag, note in (('excepcion_dt', 'observacion_dt'), ('excepcion_operador', 'observacion_operador')):
            old = cases(); setattr(old[0], flag, 'Sí'); setattr(old[0], note, 'Texto de justificación')
            save_review(self.path, old)
            new = cases(); counts = restore_review(new, load_review(self.path))
            self.assertEqual(counts['incorporadas'], 1)
            self.assertEqual(new[0].exception_tracking(), old[0].exception_tracking())

    def test_import_invalid_observation_and_operator_block_are_reported(self):
        save_review(self.path, cases())
        book = load_workbook(self.path); sheet = book['Revisión']
        sheet['I2'] = 'Sí'; sheet['J2'] = 'Justificación DT'
        sheet['K2'] = 'Sí'; sheet['L2'] = 'Intento operador'
        book.save(self.path); book.close()
        new = cases(); counts = restore_review(new, load_review(self.path))
        self.assertEqual(counts['operador_bloqueado'], 1)
        self.assertEqual(new[0].exception_tracking(), ('Sí', 'Justificación DT', 'No', ''))
        book = load_workbook(self.path); sheet = book['Revisión']
        sheet['J2'] = ' '; sheet['K2'] = 'No'; sheet['L2'] = ''
        book.save(self.path); book.close()
        new = cases(); counts = restore_review(new, load_review(self.path))
        self.assertEqual(counts['excepciones_invalidas'], 1)
        self.assertEqual(new[0].excepcion_dt, 'No')

    def test_existing_operator_observation_is_not_silently_replaced(self):
        old = cases(); old[0].excepcion_operador = 'Sí'; old[0].observacion_operador = 'Anterior'
        save_review(self.path, old)
        new = cases(); new[0].observacion_operador = 'Actual'
        counts = restore_review(new, load_review(self.path))
        self.assertEqual(counts['conflictos'], 1)
        self.assertEqual(new[0].observacion_operador, 'Actual')


if __name__ == '__main__':
    unittest.main()
