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
from qgis.PyQt.QtWidgets import QMessageBox, QPushButton
from openpyxl import load_workbook
from qgis_control_calidad import dialog as module
from qgis_control_calidad.review import build_cases, digest
from qgis_control_calidad.report_exceptions import HEADERS

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

    def cleanup(self):
        self.owner.review_dirty = False
        self.owner.close()

    def test_record_review_window_is_removed(self):
        self.assertFalse(hasattr(self.owner, 'review_viewer'))
        self.assertFalse(hasattr(self.owner, 'open_review_viewer'))
        self.assertNotIn('Revisar hallazgos', [button.text() for button in self.owner.findChildren(QPushButton)])

    def test_each_export_has_four_editable_exception_fields(self):
        self.owner.review_cases[0].excepcion_dt = 'Sí'
        self.owner.review_cases[0].observacion_dt = 'Documentado por DT'
        with patch.object(module.QFileDialog, 'getExistingDirectory', return_value=self.directory.name):
            self.owner.export_excel()
        files = list(Path(self.directory.name).glob('*.xlsx'))
        self.assertEqual(len(files), 2)
        for path in files:
            book = load_workbook(path)
            if 'regla_1' not in book.sheetnames:
                self.assertNotIn('Revisión', book.sheetnames)
                self.assertNotIn('_Identidades', book.sheetnames)
                self.assertIn('Resumen ejecutivo', book.sheetnames)
                book.close()
                continue
            self.assertIn('Revisión', book.sheetnames)
            sheet = book['Revisión']
            self.assertEqual(sheet.max_row, 3)
            for header in HEADERS:
                self.assertIn(header, [cell.value for cell in sheet[1]])
            if 'regla_1' not in book.sheetnames:
                self.assertEqual(sheet['I2'].value, 'Sí')
                self.assertEqual(sheet['J2'].value, 'Documentado por DT')
            self.assertTrue(sheet.protection.sheet)
            if 'regla_1' in book.sheetnames:
                detail = book['regla_1']
                cols = {cell.value: cell.column for cell in detail[4]}
                self.assertEqual(detail.cell(5, cols[HEADERS[0]]).value, 'Sí')
                self.assertEqual(detail.cell(5, cols[HEADERS[0]]).fill.fgColor.rgb, '00C6EFCE')
                self.assertEqual(detail.cell(5, cols[HEADERS[0]]).font.color.rgb, '00006100')
                self.assertEqual(detail.cell(6, cols[HEADERS[0]]).fill.fgColor.rgb, '00FFC7CE')
                self.assertEqual(detail.cell(5, cols[HEADERS[1]]).value, 'Documentado por DT')
                for header in HEADERS:
                    self.assertFalse(detail.cell(5, cols[header]).protection.locked)
                self.assertTrue(sheet['I2'].data_type == 'f')
                self.assertTrue(sheet['I2'].protection.locked)
                self.assertTrue(detail.protection.sheet)
                self.assertEqual(len(detail.data_validations.dataValidation), 2)
                for validation in detail.data_validations.dataValidation:
                    self.assertEqual(validation.type, 'list')
                    self.assertFalse(validation.showDropDown)
                    self.assertEqual(validation.formula1, '"Sí,No"')
            book.close()
        self.assertEqual(self.result.status, 'Correcta')

    def test_component_report_can_recover_its_operator_review(self):
        from qgis_control_calidad.review import load_review, restore_review
        with patch.object(module.QFileDialog, 'getExistingDirectory', return_value=self.directory.name):
            self.owner.export_excel()
        package = next(Path(self.directory.name).glob('detalle_Administrativas_*.xlsx'))
        book = load_workbook(package)
        sheet = book['regla_1']
        cols = {cell.value: cell.column for cell in sheet[4]}
        sheet.cell(5, cols['Excepción operador'], 'Sí')
        sheet.cell(5, cols['Observación operador'], 'Justificación del operador')
        book.save(package); book.close()
        new = build_cases(self.owner.results, self.owner.review_context)
        counts = restore_review(new, load_review(package))
        self.assertEqual(counts['incorporadas'], 1)
        self.assertEqual(new[0].excepcion_operador, 'Sí')
        self.assertEqual(new[0].observacion_operador, 'Justificación del operador')

    def test_rule_sheet_reordering_does_not_change_recovery(self):
        from qgis_control_calidad.review import load_review, restore_review
        with patch.object(module.QFileDialog, 'getExistingDirectory', return_value=self.directory.name):
            self.owner.export_excel()
        path = next(Path(self.directory.name).glob('detalle_Administrativas_*.xlsx'))
        book = load_workbook(path); sheet = book['regla_1']
        columns = {cell.value: cell.column for cell in sheet[4]}
        sheet.cell(5, columns['Excepción DT'], 'Sí')
        sheet.cell(5, columns['Observación DT'], 'Justificado DT')
        rows = list(sheet.iter_rows(min_row=5, max_row=6, values_only=True))
        for index, values in enumerate(reversed(rows), 5):
            for column, value in enumerate(values, 1):
                sheet.cell(index, column).value = value
        book.save(path); book.close()
        current = build_cases(self.owner.results, self.owner.review_context)
        counts = restore_review(current, load_review(path))
        self.assertEqual(counts['incorporadas'], 1)
        self.assertEqual(current[0].excepcion_dt, 'Sí')
        self.assertEqual(current[1].excepcion_dt, 'No')

    def test_modified_rule_data_prevents_recovery(self):
        from qgis_control_calidad.review import load_review, restore_review
        with patch.object(module.QFileDialog, 'getExistingDirectory', return_value=self.directory.name):
            self.owner.export_excel()
        path = next(Path(self.directory.name).glob('detalle_Administrativas_*.xlsx'))
        book = load_workbook(path); sheet = book['regla_1']
        columns = {cell.value: cell.column for cell in sheet[4]}
        sheet.cell(5, columns['Excepción DT'], 'Sí')
        sheet.cell(5, columns['Observación DT'], 'Justificado DT')
        sheet.cell(5, columns['numero_predial'], '99999')
        book.save(path); book.close()
        current = build_cases(self.owner.results, self.owner.review_context)
        counts = restore_review(current, load_review(path))
        self.assertEqual(counts['datos_invalidos'], 1)
        self.assertEqual(counts['incorporadas'], 0)

    def test_excel_normalized_consolidation_formulas_do_not_block_source_review(self):
        from qgis_control_calidad.review import load_review, restore_review
        with patch.object(module.QFileDialog, 'getExistingDirectory', return_value=self.directory.name):
            self.owner.export_excel()
        path = next(Path(self.directory.name).glob('detalle_Administrativas_*.xlsx'))
        book = load_workbook(path); sheet = book['regla_1']
        columns = {cell.value: cell.column for cell in sheet[4]}
        sheet.cell(5, columns['Excepción DT'], 'Sí')
        sheet.cell(5, columns['Observación DT'], 'Justificación DT')
        for col in range(9, 13):
            cell = book['Revisión'].cell(2, col)
            cell.value = cell.value.replace("'regla_1'!", 'regla_1!')
        book.save(path); book.close()
        current = build_cases(self.owner.results, self.owner.review_context)
        counts = restore_review(current, load_review(path))
        self.assertEqual(counts['incorporadas'], 1)
        self.assertEqual(current[0].excepcion_dt, 'Sí')

    def test_five_detail_buttons_load_and_reload_independently(self):
        from qgis_control_calidad.review import save_review
        components = ('Administrativas', 'Economicas', 'Estructura', 'Fisicas', 'Juridicas')
        self.owner.results = [module.RuleResult('r1', c, 'Correcta', 1,
            rows=[{'numero_predial': '00001', 'dato': c}], criterion_hash=digest(c)) for c in components]
        self.owner.review_cases = build_cases(self.owner.results, self.owner.review_context)
        self.owner.finished()
        self.assertEqual(set(self.owner.detail_review_rows), set(components))
        paths = {}
        for index, component in enumerate(components):
            path = str(Path(self.directory.name) / (component + '.xlsx'))
            cases = build_cases([self.owner.results[index]], self.owner.review_context)
            cases[0].excepcion_dt = 'Sí'; cases[0].observacion_dt = 'DT: ' + component
            save_review(path, cases)
            paths[component] = path
            load, state = self.owner.detail_review_rows[component]
            self.assertIn('No cargado', state.text())
            with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(path, 'Excel')), patch.object(module.QMessageBox, 'information'):
                load.click()
            self.assertIn('Cargado', state.text())
        self.assertTrue(all(case.excepcion_dt == 'Sí' for case in self.owner.review_cases))
        component = 'Administrativas'
        book = load_workbook(paths[component]); book['Revisión']['I2'] = 'No'; book['Revisión']['J2'] = ''
        book.save(paths[component]); book.close()
        with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(paths[component], 'Excel')), patch.object(module.QMessageBox, 'information'):
            self.owner.detail_review_rows[component][0].click()
        self.assertEqual(self.owner.review_cases[0].excepcion_dt, 'No')
        self.assertTrue(all(case.excepcion_dt == 'Sí' for case in self.owner.review_cases[1:]))
        self.assertIn('Cargado', self.owner.detail_review_rows[component][1].text())
        # The file is not held open and can be edited and saved in place.
        book = load_workbook(paths[component]); book['Revisión']['I2'] = 'Sí'; book['Revisión']['J2'] = 'DT corregida'
        book.save(paths[component]); book.close()
        with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(paths[component], 'Excel')), patch.object(module.QMessageBox, 'information'):
            self.owner.detail_review_rows[component][0].click()
        self.assertEqual(self.owner.review_cases[0].observacion_dt, 'DT corregida')

    def test_failed_detail_load_is_visible_without_losing_loaded_review(self):
        from qgis_control_calidad.review import save_review
        path = str(Path(self.directory.name) / 'admin.xlsx')
        cases = build_cases(self.owner.results, self.owner.review_context)
        cases[0].excepcion_dt = 'Sí'; cases[0].observacion_dt = 'DT válida'
        save_review(path, cases)
        with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(path, 'Excel')), patch.object(module.QMessageBox, 'information'):
            self.owner.recover_detail('Administrativas')
        with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(path + '.missing', 'Excel')), patch.object(module.QMessageBox, 'warning'):
            self.owner.recover_detail('Administrativas')
        self.assertIn('Error de carga', self.owner.detail_review_rows['Administrativas'][1].text())
        self.assertEqual(self.owner.review_cases[0].observacion_dt, 'DT válida')

    def test_statistics_refresh_on_load_reload_clear_and_discard(self):
        from qgis_control_calidad.review import save_review
        path = str(Path(self.directory.name) / 'admin.xlsx')
        cases = build_cases(self.owner.results, self.owner.review_context)
        cases[0].excepcion_dt = 'Sí'; cases[0].observacion_dt = 'DT válida'
        save_review(path, cases)
        self.assertEqual(self.owner.table.item(0, 5).text(), '2')
        def load():
            with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(path, 'Excel')), patch.object(module.QMessageBox, 'information'):
                self.owner.recover_detail('Administrativas')
        load()
        self.assertEqual(self.owner.table.item(0, 2).text(), '2')
        self.assertEqual(self.owner.table.item(0, 5).text(), '1')
        self.assertEqual(self.owner.table.item(0, 3).text(), '1')
        self.assertIn('1 errores', self.owner.summary.text())
        cases[1].excepcion_operador = 'Sí'; cases[1].observacion_operador = 'Operador válida'
        save_review(path, cases)
        load()
        self.assertEqual(self.owner.table.item(0, 5).text(), '1')
        self.assertEqual(self.owner.table.item(0, 3).text(), '1')
        self.assertEqual(self.owner.table.item(0, 4).text(), '1')
        for case in cases:
            case.excepcion_dt = 'No'; case.observacion_dt = ''
            case.excepcion_operador = 'No'; case.observacion_operador = ''
        save_review(path, cases)
        load()
        self.assertEqual(self.owner.table.item(0, 5).text(), '2')
        self.assertEqual(self.owner.table.item(0, 3).text(), '0')
        cases[0].excepcion_dt = 'Sí'; cases[0].observacion_dt = 'DT válida'
        save_review(path, cases)
        load()
        with patch.object(module.QMessageBox, 'question', return_value=QMessageBox.Discard):
            self.owner.confirm_review_changes()
        self.assertEqual(self.owner.table.item(0, 5).text(), '2')
        self.assertEqual(self.owner.table.item(0, 3).text(), '0')
        self.assertEqual(self.owner.table.item(0, 6).text(), '0')

    def test_manual_connection_fields_are_not_clipped_after_mode_changes(self):
        self.owner.show()
        app.processEvents()
        for mode in (1, 0, 1):
            self.owner.connection_mode.setCurrentIndex(mode)
            app.processEvents()
            app.processEvents()
            page = self.owner.connection_stack.currentWidget()
            self.assertGreaterEqual(page.height(), page.layout().minimumSize().height())
            controls = self.owner.schema_controls
            self.assertGreaterEqual(controls.height(), controls.minimumSizeHint().height())
            self.assertLessEqual(controls.y() + controls.height(), page.height())
            self.assertTrue(self.owner.schema.isVisible())

    def test_minimize_keeps_reviews_and_pending_changes(self):
        from qgis.PyQt.QtCore import Qt
        self.assertTrue(self.owner.windowFlags() & Qt.WindowMinimizeButtonHint)
        self.owner.review_cases[0].observacion_dt = 'No perder al minimizar'
        self.owner.review_dirty = True
        self.owner.show()
        self.owner.showMinimized()
        app.processEvents()
        self.assertTrue(self.owner.isMinimized())
        self.assertEqual(self.owner.review_cases[0].observacion_dt, 'No perder al minimizar')
        self.assertTrue(self.owner.review_dirty)
        self.owner.showNormal()
        app.processEvents()
        self.assertFalse(self.owner.isMinimized())

    def test_plugin_action_restores_minimized_window(self):
        from qgis_control_calidad.plugin import ControlCalidadPlugin
        plugin = ControlCalidadPlugin(None)
        plugin.dialog = MagicMock()
        plugin.dialog.isMinimized.return_value = True
        plugin.open_dialog()
        plugin.dialog.showNormal.assert_called_once()
        plugin.dialog.show.assert_not_called()
        plugin.dialog.activateWindow.assert_called_once()

    def test_detail_import_warns_only_dt_counts_and_operator_does_not_discount(self):
        from qgis_control_calidad.review import save_review
        path = str(Path(self.directory.name) / 'operator.xlsx')
        current = build_cases(self.owner.results, self.owner.review_context)
        current[0].excepcion_operador = 'Sí'; current[0].observacion_operador = 'Propuesta operador'
        save_review(path, current)
        with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(path, 'Excel')), patch.object(module.QMessageBox, 'information') as notice:
            self.owner.recover_detail('Administrativas')
        self.assertIn(module.EXCEPTION_NOTICE, notice.call_args.args[2])
        self.assertEqual(module.EXCEPTION_NOTICE, 'Solo las excepciones validadas y marcadas por DT descuentan errores.')
        self.assertEqual(self.owner.table.item(0, 4).text(), '1')
        self.assertEqual(self.owner.table.item(0, 5).text(), '2')

    def test_help_opens_local_guide_inside_plugin(self):
        self.assertEqual(self.owner.main_tabs.currentIndex(), 0)
        self.owner.help_button.click()
        self.assertEqual(self.owner.main_tabs.currentIndex(), 1)
        self.assertEqual(self.owner.main_tabs.tabText(1), 'Ayuda')
        self.assertIn('Validador Consistencia Lógica Alfanumérica', self.owner.help_browser.toPlainText())
        self.assertFalse(self.owner.help_browser.openExternalLinks())
        self.assertFalse(self.owner.help_browser.openLinks())
        self.assertTrue(self.owner.help_browser.isReadOnly())
        self.assertFalse(hasattr(module, 'QDesktopServices'))

    def test_help_missing_guide_stays_inside_plugin(self):
        with patch.object(module.Path, 'read_text', side_effect=OSError('missing')):
            self.owner.load_help_content()
        self.assertIn('Reinstale el ZIP', self.owner.help_browser.toPlainText())

    def test_help_search_and_contents_navigation(self):
        self.owner.help_search.setText('TEMP')
        self.owner.find_help_text()
        self.assertEqual(self.owner.help_browser.textCursor().selectedText().casefold(), 'temp')
        self.owner.navigate_help(module.QUrl('#6-interpretar-las-estadísticas'))
        self.assertIn('Interpretar las estadísticas', self.owner.help_browser.textCursor().selectedText())

    def test_release_buttons_are_not_present_in_details_or_references(self):
        self.assertNotIn('Liberar', [button.text() for button in self.owner.findChildren(QPushButton)])
        self.assertFalse(hasattr(self.owner, 'release_reference_button'))
        for load, status in self.owner.detail_review_rows.values():
            self.assertIn(load.text(), ('Cargar', 'Recargar'))
            self.assertIn('cargado', status.text().casefold())

    def test_consolidated_review_controls_and_save_prompt_are_removed(self):
        labels = [button.text() for button in self.owner.findChildren(QPushButton)]
        self.assertNotIn('Guardar revisión en Excel', labels)
        self.assertNotIn('Cargar revisión consolidada', labels)
        self.assertFalse(hasattr(self.owner, 'save_review_excel'))
        self.assertFalse(hasattr(self.owner, 'recover_review'))
        self.owner.review_dirty = True
        with patch.object(module.QMessageBox, 'question', return_value=QMessageBox.Cancel) as question:
            self.assertFalse(self.owner.confirm_review_changes())
        buttons = question.call_args.args[3]
        self.assertFalse(buttons & QMessageBox.Save)
        self.assertTrue(buttons & QMessageBox.Cancel)

    def test_statistical_summary_cannot_be_loaded_as_review_detail(self):
        with patch.object(module.QFileDialog, 'getExistingDirectory', return_value=self.directory.name):
            self.owner.export_excel()
        path = next(Path(self.directory.name).glob('resumen_control_calidad_*.xlsx'))
        previous = [case.exception_tracking() for case in self.owner.review_cases]
        with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(str(path), 'Excel')), patch.object(module.QMessageBox, 'warning') as warning:
            self.owner.recover_detail('Administrativas')
        warning.assert_called_once()
        self.assertEqual(self.owner.review_imports.sources, {})
        self.assertEqual(previous, [case.exception_tracking() for case in self.owner.review_cases])

    def test_reselect_same_model_and_switch_model_clear_environment_and_sql(self):
        with patch.object(self.owner, 'open_sql_version_dialog') as chooser:
            self.owner.environment.setCurrentText(module.SNC_ENVIRONMENT)
            self.owner.selected_sql_version = {'codigo': 'v1'}
            self.owner.model.activated.emit(self.owner.model.currentIndex())
            self.assertEqual(self.owner.environment.currentIndex(), 0)
            self.assertIsNone(self.owner.selected_sql_version)
            self.assertFalse(self.owner.choose_sql_version.isEnabled())
            chooser.reset_mock()
            self.owner.model.setCurrentText('CICA')
            chooser.assert_not_called()
        self.assertEqual(self.owner.sql_version_label.text(), 'Seleccione una versión de SQL')

    def test_discard_restores_dt_and_operator_fields(self):
        self.owner.review_cases[0].excepcion_dt = 'Sí'
        self.owner.review_cases[0].observacion_dt = 'Importado'
        self.owner.review_dirty = True
        with patch.object(module.QMessageBox, 'question', return_value=QMessageBox.Cancel):
            event = QCloseEvent(); self.owner.closeEvent(event)
            self.assertFalse(event.isAccepted())
        with patch.object(module.QMessageBox, 'question', return_value=QMessageBox.Discard):
            event = QCloseEvent(); self.owner.closeEvent(event)
            self.assertTrue(event.isAccepted())
        self.assertEqual(self.owner.review_cases[0].exception_tracking(), ('No', '', 'No', ''))

    @patch.object(module.psycopg2, 'connect')
    def test_worker_captures_sql_fingerprint_and_preserves_duplicate_columns(self, connect):
        cursor = MagicMock()
        connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = cursor
        cursor.description = [SimpleNamespace(name='id'), SimpleNamespace(name='id')]
        cursor.fetchall.return_value = [(1, 2)]
        worker = module.RuleWorker({}, 'test', '', '', [('Administrativas', 'r1', 'SELECT * FROM {esquema}predio', '')])
        captured = []; worker.result.connect(captured.append); worker.run()
        self.assertEqual(captured[0].rows, [{'id': 1, 'id__2': 2}])
        self.assertFalse(captured[0].identity_safe)
        self.assertEqual(captured[0].criterion_hash, digest('SELECT * FROM test.predio'))


if __name__ == '__main__':
    unittest.main()
