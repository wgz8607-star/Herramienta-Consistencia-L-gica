from types import SimpleNamespace
import unittest
from unittest.mock import patch
from qgis_control_calidad.dialog import ControlCalidadDialog, RuleWorker
from qgis_control_calidad.validation_performance import optimize_temporary_tables, RULE_TIMEOUT_SECONDS
from test_temporary_references import FakeConnection, FakeCursor, render, app


class ValidationPerformanceTests(unittest.TestCase):
    def test_only_session_tables_are_indexed_and_analyzed(self):
        class Cursor:
            def __init__(self):
                self.statements = []
                self.description = []
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def execute(self, statement):
                query = render(statement); self.statements.append(query)
                if query.startswith('SELECT'):
                    self.description = [SimpleNamespace(name=name) for name in ('numero_predial', 'estado', 'etapa', 'geom')]
        cursor = Cursor()
        connection = SimpleNamespace(cursor=lambda: cursor)
        optimize_temporary_tables(connection, {'cica_predio'}, {'cica_predio': 'geom'})
        statements = cursor.statements
        self.assertTrue(any('ON "pg_temp"."cica_predio" ("numero_predial")' in query for query in statements))
        self.assertTrue(any('btrim("numero_predial"::text)' in query for query in statements))
        self.assertTrue(any('USING GIST ("geom")' in query for query in statements))
        self.assertTrue(any(query.startswith('ANALYZE "pg_temp"."cica_predio"') for query in statements))
        self.assertFalse(any('public.' in query or 'snc_cica_copy.' in query for query in statements))

    def test_rule_timeout_is_recorded_and_limits_reapplied_after_rollback(self):
        class Timeout(Exception): pgcode = '57014'
        class Cursor(FakeCursor):
            def execute(self, statement):
                if render(statement) == 'TIMEOUT_RULE':
                    self.connection.events.append(('sql', 'TIMEOUT_RULE'))
                    raise Timeout('canceling statement due to statement timeout')
                return super().execute(statement)
        class Connection(FakeConnection):
            def cursor(self): return Cursor(self)
        connection = Connection()
        worker = RuleWorker({}, 'base', '', '', [
            ('Administrativas', 'regla_1_12', 'TIMEOUT_RULE', ''),
            ('Administrativas', 'regla_1_13', 'SELECT 1', '')])
        results, messages, progress = [], [], []
        worker.result.connect(results.append); worker.message.connect(messages.append)
        worker.progress.connect(lambda current, total: progress.append((current, total)))
        with patch('qgis_control_calidad.dialog.psycopg2.connect', return_value=connection):
            worker.run()
        self.assertEqual([result.status for result in results], ['Error', 'Correcta'])
        self.assertIn('regla_1_12', results[0].detail)
        self.assertIn(str(RULE_TIMEOUT_SECONDS), results[0].detail)
        queries = [event[1] for event in connection.events if event[0] == 'sql']
        self.assertEqual(sum('SET LOCAL statement_timeout' in query for query in queries), 2)
        self.assertEqual(sum('SET LOCAL lock_timeout' in query for query in queries), 2)
        self.assertEqual(progress, [(1, 2), (2, 2)])
        self.assertTrue(any('regla_1_12 (1 de 2)' in message for message in messages))
        self.assertTrue(any('regla_1_13 (2 de 2)' in message for message in messages))
        self.assertTrue(connection.closed)

    def test_progress_preserves_actual_rule_name_and_shows_elapsed_time(self):
        widget = ControlCalidadDialog()
        try:
            widget.controls_running = True
            with patch('qgis_control_calidad.dialog.time.monotonic', return_value=10):
                widget.update_worker_message('Ejecutando Administrativas · regla_1_12 (12 de 147)…')
            widget.set_progress(11, 147)
            with patch('qgis_control_calidad.dialog.time.monotonic', return_value=75):
                widget.refresh_validation_elapsed()
            self.assertIn('regla_1_12', widget.status.text())
            self.assertIn('01:05 transcurridos', widget.status.text())
            self.assertEqual(widget.progress.value(), 11)
        finally:
            widget.controls_running = False
            widget.execution_status_timer.stop()
            widget.close()
