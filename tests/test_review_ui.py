import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis.core import QgsApplication
from qgis.PyQt.QtGui import QCloseEvent
from qgis.PyQt.QtWidgets import QMessageBox
from openpyxl import load_workbook
from qgis_control_calidad import dialog as module
from qgis_control_calidad.review import ADJUST, EXCEPTION, PENDING, build_cases, digest, save_review
from qgis_control_calidad.review_dialog import ReviewDialog

app = QgsApplication.instance() or QgsApplication([], False)
app.initQgis()


class ReviewUiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.owner = module.ControlCalidadDialog()
        self.addCleanup(self.cleanup)
        self.result = module.RuleResult('regla_1', 'Administrativas', 'Correcta', 2,
                                       rows=[{'numero_predial': '00001', 'valor': 'dato A'},
                                             {'numero_predial': '00002', 'valor': 'dato B'}],
                                       criterion_hash=digest('SELECT criterio'))
        self.owner.results = [self.result]
        self.owner.review_context = {'model': 'CICA', 'schema': 'test'}
        self.owner.review_cases = build_cases(self.owner.results, self.owner.review_context)
        self.owner.finished()
        self.viewer = ReviewDialog(self.owner)
        self.owner.review_viewer = self.viewer

    def cleanup(self):
        self.owner.review_dirty = False
        self.viewer.current_case = None
        self.viewer.close()
        self.owner.close()

    def test_observation_is_preserved_when_switching_rows(self):
        self.viewer.table.setCurrentCell(0, 0)
        self.viewer.state.setCurrentText(EXCEPTION)
        self.viewer.observation.setPlainText('Excepción documentada')
        self.viewer.table.setCurrentCell(1, 0)
        self.assertEqual(self.owner.review_cases[0].estado_revision_usuario, EXCEPTION)
        self.assertEqual(self.owner.review_cases[0].observacion_usuario, 'Excepción documentada')
        self.assertTrue(self.owner.review_cases[0].fecha_revision_usuario)
        self.viewer.table.setCurrentCell(0, 0)
        self.assertEqual(self.viewer.observation.toPlainText(), 'Excepción documentada')
        self.assertTrue(self.owner.review_dirty)

    def test_refresh_allows_selecting_the_previously_selected_row(self):
        self.viewer.table.setCurrentCell(0, 0)
        self.viewer.refresh()
        self.assertEqual(self.viewer.table.currentRow(), -1)
        self.viewer.table.setCurrentCell(0, 0)
        self.assertEqual(self.viewer.current_case, 0)
        self.assertTrue(self.viewer.observation.isEnabled())

    def test_unjustified_exception_prevents_switch_save_and_close(self):
        self.viewer.table.setCurrentCell(0, 0)
        self.viewer.state.setCurrentText(EXCEPTION)
        self.viewer.observation.setPlainText('  ')
        with patch.object(module.QMessageBox, 'warning'):
            self.viewer.table.setCurrentCell(1, 0)
            self.assertEqual(self.viewer.table.currentRow(), 0)
            with patch.object(module.QFileDialog, 'getSaveFileName') as chooser:
                self.assertFalse(self.owner.save_review_excel())
                chooser.assert_not_called()
            event = QCloseEvent(); self.owner.closeEvent(event)
            self.assertFalse(event.isAccepted())
        self.assertEqual(self.owner.review_cases[0].estado_revision_usuario, PENDING)
        self.viewer.state.setCurrentText(PENDING)

    def test_save_includes_hidden_rows_and_editor_draft(self):
        self.viewer.table.setCurrentCell(0, 0)
        self.viewer.state.setCurrentText(EXCEPTION)
        self.viewer.observation.setPlainText('Justificación guardada')
        self.viewer.search.setText('00001')
        self.assertTrue(self.viewer.table.isRowHidden(1))
        path = str(Path(self.directory.name) / 'review.xlsx')
        with patch.object(module.QFileDialog, 'getSaveFileName', return_value=(path, 'Excel')):
            self.assertTrue(self.owner.save_review_excel())
        book = load_workbook(path)
        self.assertEqual(book['Revisión'].max_row, 3)
        self.assertEqual(book['Revisión']['F2'].value, 'Justificación guardada')
        self.assertEqual(book['Revisión']['F1'].value, 'observacion_usuario')
        book.close()
        self.assertFalse(self.owner.review_dirty)

    def test_dirty_close_cancel_and_discard(self):
        self.viewer.table.setCurrentCell(0, 0)
        self.viewer.observation.setPlainText('Edición sin guardar')
        with patch.object(module.QMessageBox, 'question', return_value=QMessageBox.Cancel):
            event = QCloseEvent(); self.owner.closeEvent(event)
            self.assertFalse(event.isAccepted())
            self.assertTrue(self.owner.review_dirty)
        with patch.object(module.QMessageBox, 'question', return_value=QMessageBox.Discard):
            event = QCloseEvent(); self.owner.closeEvent(event)
            self.assertTrue(event.isAccepted())
        self.assertEqual(self.owner.review_cases[0].tracking(), (PENDING, '', ''))
        self.assertFalse(self.owner.review_dirty)

    def test_close_save_cancel_does_not_discard_edits(self):
        self.viewer.table.setCurrentCell(0, 0)
        self.viewer.observation.setPlainText('No perder esta edición')
        with patch.object(module.QMessageBox, 'question', return_value=QMessageBox.Save), patch.object(module.QFileDialog, 'getSaveFileName', return_value=('', '')):
            event = QCloseEvent(); self.owner.closeEvent(event)
        self.assertFalse(event.isAccepted())
        self.assertTrue(self.owner.review_dirty)
        self.assertEqual(self.owner.review_cases[0].observacion_usuario, 'No perder esta edición')

    def test_recover_reports_invalid_exception_and_preserves_existing_review(self):
        path = Path(self.directory.name) / 'old.xlsx'
        old = build_cases(self.owner.results, self.owner.review_context)
        old[0].set_review(EXCEPTION, 'Anterior')
        old[1].set_review(EXCEPTION, 'Será invalidada')
        save_review(path, old)
        book = load_workbook(path); book['Revisión']['F3'] = ' '; book.save(path); book.close()
        self.owner.review_cases[0].set_review(ADJUST, 'No sobrescribir')
        self.owner.review_dirty = True
        with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(str(path), 'Excel')), patch.object(module.QMessageBox, 'information') as message:
            self.owner.recover_review()
        self.assertEqual(self.owner.review_cases[0].observacion_usuario, 'No sobrescribir')
        self.assertEqual(self.owner.review_cases[1].estado_revision_usuario, PENDING)
        text = message.call_args.args[2]
        self.assertIn('por conflicto: 1', text)
        self.assertIn('Revisión pendiente: 1', text)

    def test_reselect_same_model_and_switch_model_clear_environment_and_sql(self):
        with patch.object(self.owner, 'open_sql_version_dialog') as chooser:
            self.owner.environment.setCurrentText(module.SNC_ENVIRONMENT)
            self.owner.selected_sql_version = {'codigo': 'v1'}
            self.owner.model.activated.emit(self.owner.model.currentIndex())
            self.assertEqual(self.owner.environment.currentIndex(), 0)
            self.assertIsNone(self.owner.selected_sql_version)
            self.assertEqual(self.owner.repository_rules, [])
            self.assertFalse(self.owner.choose_sql_version.isEnabled())
            chooser.reset_mock()
            self.owner.model.setCurrentText('CICA')
            chooser.assert_not_called()
            self.assertEqual(self.owner.environment.currentIndex(), 0)
        self.assertEqual(self.owner.sql_version_label.text(), 'Seleccione una versión de SQL')

    def test_existing_detailed_report_contains_tracking_without_changing_automatic_result(self):
        self.owner.review_cases[0].set_review(EXCEPTION, 'Documentado')
        with patch.object(module.QFileDialog, 'getExistingDirectory', return_value=self.directory.name):
            self.owner.export_excel()
        packages = list(Path(self.directory.name).glob('detalle_Administrativas_*.xlsx'))
        self.assertEqual(len(packages), 1)
        book = load_workbook(packages[0])
        sheet = book['regla_1']
        headers = {cell.value: cell.column for cell in sheet[4]}
        self.assertEqual(sheet.cell(5, headers['estado_revision_usuario']).value, EXCEPTION)
        self.assertEqual(sheet.cell(5, headers['Observación']).value, 'Documentado')
        self.assertEqual(self.result.status, 'Correcta')
        book.close()

    @patch.object(module.psycopg2, 'connect')
    def test_worker_captures_sql_fingerprint_and_preserves_duplicate_columns(self, connect):
        cursor = MagicMock()
        connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = cursor
        cursor.description = [SimpleNamespace(name='id'), SimpleNamespace(name='id')]
        cursor.fetchall.return_value = [(1, 2)]
        worker = module.RuleWorker({}, 'test', '', '', [('Administrativas', 'r1', 'SELECT * FROM {esquema}predio', '')])
        captured = []
        worker.result.connect(captured.append)
        worker.run()
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0].rows, [{'id': 1, 'id__2': 2}])
        self.assertFalse(captured[0].identity_safe)
        self.assertEqual(captured[0].criterion_hash, digest('SELECT * FROM test.predio'))


if __name__ == '__main__':
    unittest.main()
