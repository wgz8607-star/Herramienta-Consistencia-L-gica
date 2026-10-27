import csv
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QDialog
from qgis_control_calidad.cica_data import prepare_csv, install_csv, resolve_csv_tables
from qgis_control_calidad.ingestion import CicaIngestionDialog
from qgis_control_calidad import dialog as module
from qgis_control_calidad.templates import validation_format
from test_temporary_references import FakeConnection, FakeCursor, render

app = QgsApplication.instance() or QgsApplication([], False)
app.initQgis()


class CicaCursor(FakeCursor):
    def execute(self, statement, params=None):
        self.params = params
        super().execute(statement)

    def fetchone(self):
        return ('test.cica_predio' if self.connection.existing else None,)


class CicaConnection(FakeConnection):
    def __init__(self, existing=False):
        super().__init__()
        self.existing = existing

    def cursor(self):
        return CicaCursor(self)


class CicaAndFormatsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def reference(self, content='numero_predial;estado\n00001;ACTIVO\n'):
        source = Path(self.directory.name) / 'predio.csv'
        source.write_text(content, encoding='utf-8-sig')
        reference = prepare_csv('cica_predio', source)
        self.addCleanup(reference.close)
        return reference, source

    def test_csv_snapshot_preserves_text_and_survives_source_change(self):
        reference, source = self.reference('Número predial;Observación\n00001;"Texto ñ; con separador"\n')
        source.unlink()
        self.assertEqual(reference.columns, ('numero_predial', 'observacion'))
        with reference.csv_path.open(encoding='utf-8', newline='') as stream:
            self.assertEqual(list(csv.reader(stream)), [['00001', 'Texto ñ; con separador']])
        reference.close()
        self.assertFalse(reference.csv_path.exists())

    def test_csv_rejects_duplicate_headers_and_invalid_width(self):
        for content in ('Nombre;Nómbre\na;b\n', 'numero_predial;estado\n0001;A;extra\n'):
            with self.assertRaises(ValueError):
                self.reference(content)

    def test_temp_copy_never_creates_persistent_tables_and_retains_types(self):
        reference, _ = self.reference()
        for existing in (False, True):
            connection = CicaConnection(existing)
            with patch('psycopg2.sql.Composed.as_string', lambda self, context: render(self)):
                install_csv(connection, reference, 'test')
            statements = [event[1] for event in connection.events if event[0] == 'sql']
            creation = next(query for query in statements if query.startswith('CREATE'))
            self.assertTrue(creation.startswith('CREATE TEMP TABLE'))
            self.assertIn('ON COMMIT PRESERVE ROWS', creation)
            self.assertEqual('LIKE "test"."cica_predio"' in creation, existing)
            self.assertNotIn('INCLUDING DEFAULTS', creation)
            copy = next(event for event in connection.events if event[0] == 'copy')
            self.assertIn('COPY pg_temp.', copy[1])
            self.assertEqual(copy[2][0][0], '00001')

    def test_worker_uses_csv_in_same_connection_after_rule_failure_and_closes(self):
        reference, _ = self.reference()
        connection = CicaConnection()
        worker = module.RuleWorker({}, 'test', '', '', [
            ('Administrativas', 'r1', 'FAIL_RULE', ''),
            ('Administrativas', 'r2', 'SELECT * FROM {esquema}.cica_predio', '')], cica_references={'cica_predio': reference})
        results = []; worker.result.connect(results.append)
        with patch.object(module.psycopg2, 'connect', return_value=connection), patch('psycopg2.sql.Composed.as_string', lambda self, context: render(self)):
            worker.run()
        queries = [event[1] for event in connection.events if event[0] == 'sql']
        self.assertIn('SELECT * FROM pg_temp.cica_predio', queries)
        self.assertEqual([r.status for r in results], ['Error', 'Correcta'])
        self.assertTrue(connection.closed)
        self.assertFalse(connection.tables)
        self.assertLess(connection.events.index(('commit',)), connection.events.index(('rollback',)))

    def test_cica_rule_1_1_uses_selected_source_mode_without_changing_logic(self):
        rule_file = Path(module.__file__).parent / 'resources/sql/rules_cica_db/Administrativas/regla_1_1.sql'
        original = rule_file.read_text(encoding='utf-8')
        temporary = module.RuleWorker({}, 'base_cica', '', '', [], cica_references={
            'cica_predio': None, 'cica_seguimiento_control': None,
        }).resolve_sql(original)
        persistent = module.RuleWorker({}, 'base_cica', '', '', []).resolve_sql(original)
        for table in ('cica_predio', 'cica_seguimiento_control'):
            self.assertIn('pg_temp.' + table, temporary)
            self.assertNotIn('base_cica.' + table, temporary)
            self.assertIn('base_cica.' + table, persistent)
        self.assertEqual(temporary.replace('pg_temp.', '{esquema}.'), original)
        self.assertEqual(persistent.replace('base_cica.', '{esquema}.'), original)

    def test_only_selected_csv_tables_are_redirected(self):
        query = 'SELECT * FROM test.cica_predio p JOIN test.cica_contacto c ON TRUE'
        self.assertEqual(resolve_csv_tables(query, 'test', {'cica_predio': None}),
                         'SELECT * FROM pg_temp.cica_predio p JOIN test.cica_contacto c ON TRUE')

    def test_redirection_preserves_literals_comments_and_unselected_tables(self):
        query = 'SELECT \'test.cica_predio\' FROM "test"."cica_predio" -- test.cica_predio\nJOIN test.cica_contacto ON TRUE'
        resolved = resolve_csv_tables(query, 'test', {'cica_predio': None})
        self.assertIn("'test.cica_predio'", resolved)
        self.assertIn('FROM pg_temp.cica_predio', resolved)
        self.assertIn('-- test.cica_predio', resolved)
        self.assertIn('JOIN test.cica_contacto', resolved)

    def test_csv_dialog_cancellation_keeps_existing_snapshot(self):
        reference, source = self.reference()
        dialog = CicaIngestionDialog(references={'cica_predio': reference})
        with patch.object(module.QFileDialog, 'getOpenFileName', return_value=(str(source), '')):
            dialog.choose_csv('Predio')
        replacement = dialog.prepared['cica_predio']
        dialog.reject(); dialog.clear_prepared()
        self.assertFalse(replacement.csv_path.exists())
        self.assertTrue(reference.csv_path.exists())

    def test_formats_use_model_v2_and_exclude_v3_and_snc(self):
        for model in ('CICA', 'Modelo Interno de Levantamiento 1.0'):
            format = validation_format(model, 'Validaciones del modelo', {'codigo': 'V2_29_07_2024'})
            self.assertIsNotNone(format)
            self.assertTrue(format[1].is_file())
            self.assertIsNone(validation_format(model, 'Validaciones del modelo', {'codigo': 'V3_07_09_2026'}))
            self.assertIsNone(validation_format(model, module.SNC_ENVIRONMENT, {'codigo': 'V2_29_07_2024'}))
            self.assertIsNone(validation_format(model, 'Validaciones del modelo', {'codigo': 'V2', 'id': {'table': 'reglas_cica_v3_07_09_2026'}}))
        self.assertIsNone(validation_format('CICA', 'Validaciones del modelo', None))

    def test_format_download_after_validation_is_an_exact_copy(self):
        owner = module.ControlCalidadDialog(); self.addCleanup(owner.close)
        owner.pending_format = validation_format('CICA', 'Validaciones del modelo', {'codigo': 'V2_29_07_2024'})
        self.assertFalse(owner.format_download.isEnabled())
        owner.results = [module.RuleResult('r1', 'Administrativas', 'Correcta', 0, rows=[])]
        owner.finished()
        self.assertTrue(owner.format_download.isEnabled())
        destination = Path(self.directory.name) / 'formato.xlsx'
        with patch.object(module.QFileDialog, 'getSaveFileName', return_value=(str(destination), '')):
            owner.download_validation_format()
        self.assertEqual(destination.read_bytes(), owner.completed_format[1].read_bytes())
        owner.results = [module.RuleResult('r1', 'Administrativas', 'Error', '—')]
        owner.finished()
        self.assertFalse(owner.format_download.isEnabled())
