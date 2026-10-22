"""Run with the QGIS Python environment and QT_QPA_PLATFORM=offscreen."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QDialog
from qgis_control_calidad import dialog as module

app = QgsApplication.instance() or QgsApplication([], False)
app.initQgis()


class SncTests(unittest.TestCase):
    def setUp(self):
        prompt = patch.object(module.QInputDialog, 'getText', return_value=('test-session-password', True))
        prompt.start()
        self.addCleanup(prompt.stop)
        self.widget = module.ControlCalidadDialog()
        self.addCleanup(self.widget.close)

    def select_model(self, model):
        with patch.object(self.widget, 'open_sql_version_dialog'):
            self.widget.model.setCurrentText(model)
            self.widget.environment.setCurrentText(module.SNC_ENVIRONMENT)

    def database(self, connect):
        cursor = MagicMock()
        connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = cursor
        return cursor

    def test_repository_password_is_masked_and_session_only(self):
        with patch.object(module.QInputDialog, 'getText', return_value=('test-session-password', True)) as prompt:
            first = self.widget.repository_connection_params()
            second = self.widget.repository_connection_params()
        self.assertEqual(first['user'], 'admin_ant')
        self.assertEqual(first['password'], second['password'])
        self.assertEqual(module.REPOSITORY_CONNECTION['password'], '')
        prompt.assert_called_once()
        self.assertEqual(prompt.call_args.args[3], module.QLineEdit.Password)

    def test_cancel_password_blocks_database_access(self):
        with patch.object(module.QInputDialog, 'getText', return_value=('', False)), patch.object(module.psycopg2, 'connect') as connect:
            self.widget.open_sql_version_dialog()
        connect.assert_not_called()
        self.assertFalse(self.widget.run_button.isEnabled())
        self.assertIsNone(self.widget._repository_password)

    def test_initial_state_and_direct_execution_are_blocked(self):
        self.assertFalse(self.widget.run_button.isEnabled())
        self.assertFalse(self.widget.category_checks)
        with patch.object(module.QMessageBox, 'warning'), patch.object(module.psycopg2, 'connect') as connect:
            self.widget.run_rules()
        connect.assert_not_called()

    def test_failed_refresh_clears_previous_rules(self):
        self.widget.selected_sql_version = {'codigo': 'v1'}
        self.widget.repository_rules = [{'type': 'CONTROL', 'component': 'Fisicas', 'sql': 'SELECT 1'}]
        self.widget.refresh_categories()
        self.assertTrue(self.widget.run_button.isEnabled())
        with patch.object(self.widget, 'repository_source', side_effect=RuntimeError('Connection failed')), patch.object(module.QMessageBox, 'information'):
            self.widget.open_sql_version_dialog()
        self.assertFalse(self.widget.run_button.isEnabled())
        self.assertEqual(self.widget.repository_rules, [])
        self.assertIsNone(self.widget.selected_sql_version)

    def test_selection_and_running_state_control_execution(self):
        self.widget.selected_sql_version = {'codigo': 'v1'}
        self.widget.repository_rules = [{'type': 'CONTROL', 'component': 'Fisicas', 'sql': 'SELECT 1'}]
        self.widget.refresh_categories()
        card = self.widget.category_checks['Fisicas']
        self.assertTrue(self.widget.run_button.isEnabled())
        card.setChecked(False)
        self.assertFalse(self.widget.run_button.isEnabled())
        card.setChecked(True)
        self.assertTrue(self.widget.run_button.isEnabled())
        self.widget.controls_running = True
        self.widget.update_run_availability()
        self.assertFalse(self.widget.run_button.isEnabled())
        self.widget.clear_repository_rules()
        self.widget.finished()
        self.assertFalse(self.widget.run_button.isEnabled())

    @patch.object(module.psycopg2, 'connect')
    def test_empty_version_cannot_enable_execution(self, connect):
        cursor = self.database(connect)
        cursor.fetchall.return_value = []
        source = {'kind': 'tables', 'tables': ['reglas_cargue_snc_cica'], 'snc': True}
        with patch.object(self.widget, 'repository_source', return_value=source), patch.object(module, 'SqlVersionDialog') as chooser:
            chooser.return_value.exec.return_value = QDialog.Accepted
            chooser.return_value.selected_version = {'id': {'table': source['tables'][0], 'version': 'v1'}, 'codigo': 'v1'}
            self.widget.open_sql_version_dialog()
        self.assertFalse(self.widget.run_button.isEnabled())

    @patch.object(module.psycopg2, 'connect')
    def test_each_model_uses_only_its_snc_table(self, connect):
        cursor = self.database(connect)
        for model, table in module.SNC_REPOSITORY_TABLES.items():
            self.select_model(model)
            cursor.fetchone.side_effect = [(table,), (True,)]
            source = self.widget.repository_source({})
            self.assertEqual(source['tables'], [table])
            self.assertTrue(source['snc'])

    @patch.object(module.psycopg2, 'connect')
    def test_missing_or_unreadable_table_never_falls_back(self, connect):
        cursor = self.database(connect)
        self.select_model('CICA')
        for answers in [[(None,)], [('table',), (False,)]]:
            cursor.fetchone.side_effect = answers
            with self.assertRaises(ValueError):
                self.widget.repository_source({})

    @patch.object(module.psycopg2, 'connect')
    def test_loaded_controls_require_explicit_opt_in(self, connect):
        self.select_model('XTF')
        source = {'kind': 'tables', 'tables': ['reglas_cargue_snc_xtf'], 'snc': True}
        cursor = self.database(connect)
        cursor.fetchall.return_value = [('Juridicas', 'snc_1', 'CONTROL', 'SELECT 1', 'Control SNC')]
        with patch.object(self.widget, 'repository_source', return_value=source), patch.object(module, 'SqlVersionDialog') as chooser:
            chooser.return_value.exec.return_value = QDialog.Accepted
            chooser.return_value.selected_version = {'id': {'table': source['tables'][0], 'version': 'v1'}, 'codigo': 'v1'}
            self.widget.open_sql_version_dialog()
        self.assertEqual(self.widget.repository_rules[0]['source_component'], 'Juridicas')
        card = self.widget.category_checks[module.SNC_CATEGORY]
        self.assertTrue(card.isEnabled())
        self.assertFalse(card.isChecked())
        self.widget.select_all_categories()
        self.assertFalse(card.isChecked())
        card.click()
        self.assertIn('1 reglas', self.widget.category_summary.text())
        query, params = cursor.execute.call_args.args
        self.assertIn('public.reglas_cargue_snc_xtf', query)
        self.assertEqual(params, ('v1',))

    @patch.object(module.psycopg2, 'connect')
    def test_versions_do_not_require_extra_timestamp_column(self, connect):
        cursor = self.database(connect)
        cursor.fetchall.return_value = [('v1', 'SNC', 'PUBLICADA', None)]
        chooser = module.SqlVersionDialog(self.widget, {}, {'kind': 'tables', 'tables': ['reglas_cargue_snc_cica'], 'snc': True, 'label': 'SNC'})
        self.addCleanup(chooser.close)
        self.assertEqual(chooser.table.rowCount(), 1)
        self.assertNotIn('fecha_actualizacion', cursor.execute.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
