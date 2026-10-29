import unittest
from types import SimpleNamespace
from unittest.mock import patch

from qgis_control_calidad import dialog as module
from qgis_control_calidad.review import build_cases
from test_temporary_references import app


class ValidationConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.widget = module.ControlCalidadDialog()
        self.addCleanup(self.cleanup)
        self.widget.environment.blockSignals(True)
        self.widget.environment.setCurrentText('Validaciones del modelo')
        self.widget.environment.blockSignals(False)
        self.widget.schema.addItem('municipio')
        self.widget.repository_rules = [{'type': 'CONTROL', 'component': 'Administrativas', 'rule': 'regla_1_1', 'sql': 'SELECT 1', 'description': 'Control'}]
        self.widget.selected_sql_version = {'codigo': 'V2_29_07_2024'}
        self.widget.refresh_categories()
        self.widget.category_checks['Administrativas'].setChecked(True)
        self.widget.update_run_availability()
        self.assertTrue(self.widget.run_button.isEnabled())
        self.params = {'dbname': 'base_catastral', 'user': 'usuario_privado', 'password': 'secreto_no_mostrar'}

    def cleanup(self):
        self.widget.review_dirty = False
        self.widget.close()

    def test_cancel_preserves_results_followup_and_metadata_without_starting_worker(self):
        previous = module.RuleResult('anterior', 'Administrativas', 'Correcta', 1, rows=[{'numero_predial': '00001'}])
        self.widget.results = [previous]
        self.widget.review_cases = build_cases(self.widget.results, {})
        self.widget.review_cases[0].observacion_dt = 'Conservar'
        self.widget.execution_info = {'Fecha de ejecución': 'anterior'}
        with patch.object(self.widget, 'connection_params', return_value=self.params), \
             patch.object(self.widget, 'confirm_validation', return_value=False) as confirm, \
             patch.object(self.widget, 'commit_review_editor') as commit, \
             patch.object(self.widget, 'confirm_review_changes') as discard, \
             patch.object(module, 'RuleWorker') as worker:
            self.widget.run_rules()
        confirm.assert_called_once()
        commit.assert_not_called(); discard.assert_not_called(); worker.assert_not_called()
        self.assertIs(self.widget.results[0], previous)
        self.assertEqual(self.widget.review_cases[0].observacion_dt, 'Conservar')
        self.assertEqual(self.widget.execution_info, {'Fecha de ejecución': 'anterior'})
        self.assertFalse(self.widget.controls_running)

    def test_metadata_confirmation_precedes_existing_review_discard_prompt(self):
        events = []
        with patch.object(self.widget, 'connection_params', return_value=self.params), \
             patch.object(self.widget, 'confirm_validation', side_effect=lambda *args: events.append('metadatos') or True), \
             patch.object(self.widget, 'commit_review_editor', side_effect=lambda: events.append('editor') or True), \
             patch.object(self.widget, 'confirm_review_changes', side_effect=lambda: events.append('revision') or False), \
             patch.object(module, 'RuleWorker') as worker:
            self.widget.run_rules()
        self.assertEqual(events, ['metadatos', 'editor', 'revision'])
        worker.assert_not_called()

    def test_summary_uses_selected_filters_without_reference_rows_or_secrets(self):
        self.widget.scope_selection = 'urban+rural'
        self.widget.scope_prefixes = ('08421010000010001',)
        self.widget.temporary_references['R1'] = SimpleNamespace(filename='r1_usuario.xlsx', row_count=123, close=lambda: None)
        rules = [('Administrativas', '1_1', 'SELECT * FROM {esquema_r1}.{tabla_r1}', ''),
                 ('Administrativas', '1_2', 'SELECT 1', '')]
        rows = dict(self.widget.validation_confirmation_metadata(self.params, 'municipio', rules, None))
        self.assertEqual(rows['Base catastral a validar'], 'base_catastral')
        self.assertEqual(rows['Alcance territorial'], 'Urbano + Rural')
        self.assertEqual(rows['Manzanas / veredas (NPN 1–17)'], '08421010000010001')
        self.assertNotIn('Origen de R1/R2', rows)
        self.assertNotIn('R1', rows)
        self.assertNotIn('R2', rows)
        self.assertEqual(rows['Total de reglas'], '2')
        text = str(rows)
        self.assertNotIn(self.params['password'], text); self.assertNotIn(self.params['user'], text)
        self.assertNotIn('SELECT', text)

    def test_reference_and_report_general_rows_are_omitted(self):
        with patch.object(self.widget, 'load_current_references'):
            self.widget.reference_mode.setCurrentIndex(1)
        current = {'divipola': '08421', 'municipality': 'Luruaco', 'date': '2026-09-30',
                   'tables': {'R1': '08421_20260930_r1', 'R2': '08421_20260930_r2'}}
        rows = dict(self.widget.validation_confirmation_metadata(self.params, 'municipio', [], current,
                    'SELECT * FROM {esquema_r2}.{tabla_r2}'))
        self.assertNotIn('Municipio de R1/R2', rows)
        self.assertNotIn('Fecha R1/R2 vigente', rows)
        self.assertNotIn('R1', rows)
        self.assertNotIn('R2', rows)
        self.assertNotIn('Reporte general', rows)
