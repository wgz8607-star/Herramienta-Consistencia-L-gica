import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from qgis_control_calidad import dialog as module
from qgis_control_calidad.cica_data import prepare_csv
from test_temporary_references import app


class CicaAutomaticConnectionTests(unittest.TestCase):
    def setUp(self):
        self.widget = module.ControlCalidadDialog()
        self.addCleanup(self.cleanup)
    def cleanup(self):
        self.widget.controls_running = False
        self.widget.review_dirty = False
        self.widget.close()

    def test_connection_controls_hide_for_cica_and_return_for_internal_model(self):
        self.widget.schema.addItem('old_internal_schema')
        self.widget.model.setCurrentText('CICA')
        for item in (self.widget.connection_mode_label, self.widget.connection_mode,
                     self.widget.connection_stack, self.widget.schema_controls):
            self.assertTrue(item.isHidden())
        self.assertEqual(self.widget.left_tabs.tabText(0), 'Fuente de datos')
        self.assertEqual(self.widget.validation_schema(), 'pg_temp')
        params = {'dbname': 'sentencias', 'host': 'service'}
        with patch.object(self.widget, 'repository_connection_params', return_value=params), \
             patch.object(self.widget, 'qgis_connection_params') as qgis:
            self.assertEqual(self.widget.connection_params(), params)
        qgis.assert_not_called()
        self.widget.model.setCurrentIndex(0)
        self.assertFalse(self.widget.connection_mode.isHidden())
        self.assertFalse(self.widget.connection_stack.isHidden())
        self.assertFalse(self.widget.schema_controls.isHidden())
        self.assertEqual(self.widget.validation_schema(), 'old_internal_schema')

    def test_cica_runs_without_hidden_schema_or_qgis_connection(self):
        self.widget.model.setCurrentText('CICA')
        self.widget.environment.blockSignals(True)
        self.widget.environment.setCurrentText('Validaciones del modelo')
        self.widget.environment.blockSignals(False)
        self.widget.repository_rules = [{'type': 'CONTROL', 'component': 'Administrativas', 'rule': 'regla_1_1', 'sql': 'SELECT * FROM {esquema}.cica_predio', 'description': ''}]
        self.widget.selected_sql_version = {'codigo': 'V2'}
        self.widget.refresh_categories()
        self.widget.category_checks['Administrativas'].setChecked(True)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'predio.csv'
            source.write_text('numero_predial;estado\n084210100000000000000000000000;ACTIVO\n')
            ref = prepare_csv('cica_predio', source)
            self.widget.cica_references['cica_predio'] = ref
            params = {'dbname': 'sentencias'}
            with patch.object(self.widget, 'repository_connection_params', return_value=params), \
                 patch.object(self.widget, 'qgis_connection_params') as qgis, \
                 patch.object(self.widget, 'confirm_validation', return_value=True), \
                 patch.object(self.widget, 'resolve_validation_context', return_value='LURUACO'), \
                 patch.object(module, 'RuleWorker') as worker, patch.object(module, 'QThread'):
                self.widget.run_rules()
            qgis.assert_not_called()
            worker.assert_called_once()
            self.assertEqual(worker.call_args.args[0], params)
            self.assertEqual(worker.call_args.args[1], 'pg_temp')
            self.assertEqual(worker.call_args.kwargs['cica_references']['cica_predio'], ref)
            ref.close();self.widget.cica_references = {}

    def test_cica_location_reads_selected_snapshot_not_persistent_ilc_predio(self):
        self.widget.model.setCurrentText('CICA')
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'predio.csv'
            source.write_text('numero_predial;estado\n084210100000000000000000000000;ACTIVO\n')
            ref = prepare_csv('cica_predio', source)
            self.widget.cica_references['cica_predio'] = ref
            with patch.object(module.psycopg2, 'connect') as connection:
                location = self.widget.resolve_validation_context({}, 'pg_temp')
            connection.assert_not_called()
            self.assertIn('LURUACO (08421)', location)
            ref.close();self.widget.cica_references = {}
