import threading
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from qgis_control_calidad.dialog import ControlCalidadDialog, RuleWorker, RuleResult
from qgis_control_calidad.review import build_cases
from test_temporary_references import FakeConnection, FakeCursor, render, app


class InterruptTests(unittest.TestCase):
    def test_interrupt_cancels_only_active_connection_and_skips_remaining_queries(self):
        entered = threading.Event(); released = threading.Event()
        class Cancelled(Exception): pgcode = '57014'
        class Cursor(FakeCursor):
            def execute(self, statement):
                if render(statement) == 'BLOCK_RULE':
                    self.connection.events.append(('sql', 'BLOCK_RULE')); entered.set()
                    if not released.wait(3): raise RuntimeError('Cancel was not delivered')
                    raise Cancelled('canceling statement due to user request')
                return super().execute(statement)
        class Connection(FakeConnection):
            def __init__(self): super().__init__(); self.cancel_calls = 0
            def cursor(self): return Cursor(self)
            def cancel(self): self.cancel_calls += 1; released.set()
        connection = Connection(); unrelated = Connection()
        worker = RuleWorker({}, 'base', '', '', [
            ('Administrativas', 'regla_1_1', 'SELECT 1', ''),
            ('Administrativas', 'regla_1_2', 'BLOCK_RULE', ''),
            ('Administrativas', 'regla_1_3', 'NEVER_RUN', '')], general_report_path='NEVER_REPORT')
        result = []; cancelled = []; finished = []; errors = []
        # Direct connections make capture deterministic when run() is called in a Python thread.
        from qgis.PyQt.QtCore import Qt
        worker.result.connect(result.append, Qt.DirectConnection)
        worker.cancelled.connect(lambda: cancelled.append(True), Qt.DirectConnection)
        worker.finished.connect(lambda: finished.append(True), Qt.DirectConnection)
        worker.fatal_error.connect(errors.append, Qt.DirectConnection)
        with patch('qgis_control_calidad.dialog.psycopg2.connect', return_value=connection):
            thread = threading.Thread(target=worker.run)
            thread.start()
            try:
                self.assertTrue(entered.wait(2))
                worker.request_cancel(); worker.request_cancel()
                thread.join(2)
                self.assertFalse(thread.is_alive())
            finally:
                released.set(); thread.join(4)
        worker.cancel_thread.join(1)
        self.assertEqual([item.rule for item in result], ['regla_1_1'])
        self.assertEqual(cancelled, [True]); self.assertEqual(finished, [True]); self.assertEqual(errors, [])
        self.assertGreater(connection.cancel_calls, 0); self.assertEqual(unrelated.cancel_calls, 0)
        self.assertTrue(connection.closed); self.assertTrue(worker.run_done.is_set())
        queries = [event[1] for event in connection.events if event[0] == 'sql']
        self.assertNotIn('NEVER_RUN', queries); self.assertNotIn('NEVER_REPORT', queries)

    def test_cancel_before_worker_starts_never_opens_database(self):
        worker = RuleWorker({}, 'base', '', '', [('Administrativas', 'regla_1_1', 'SELECT 1', '')])
        cancelled = []; worker.cancelled.connect(lambda: cancelled.append(True))
        worker.request_cancel()
        with patch('qgis_control_calidad.dialog.psycopg2.connect') as connection:
            worker.run()
        connection.assert_not_called(); self.assertEqual(cancelled, [True])
        worker.cancel_thread.join(1)

    def test_interrupted_ui_keeps_partial_progress_and_disables_reports(self):
        widget = ControlCalidadDialog()
        try:
            widget.results = [RuleResult('regla_1_1', 'Administrativas', 'Correcta', 1, rows=[{'numero_predial': '08421010001'}])]
            widget.review_cases = build_cases(widget.results, {})
            widget.controls_running = True
            widget.worker = SimpleNamespace(request_cancel=MagicMock())
            widget.progress.setRange(0, 3); widget.progress.setValue(1)
            widget.interrupt_button.setEnabled(True)
            widget.interrupt_validation(); widget.interrupt_validation()
            widget.worker.request_cancel.assert_called_once()
            self.assertFalse(widget.interrupt_button.isEnabled())
            widget.mark_validation_interrupted(); widget.finished()
            self.assertEqual(widget.progress.value(), 1)
            self.assertIn('interrumpida', widget.status.text())
            self.assertIn('Resultados parciales', widget.summary.text())
            self.assertFalse(widget.export_button.isEnabled()); self.assertFalse(widget.format_download.isEnabled())
            self.assertEqual(widget.execution_info['Estado de ejecución'], 'Interrumpida por el usuario')
            with self.assertRaisesRegex(ValueError, 'interrumpida'):
                widget.build_detail_reports()
        finally:
            widget.controls_running = False; widget.execution_status_timer.stop(); widget.close()

    def test_interrupt_also_cancels_current_reference_read_connection(self):
        entered = threading.Event(); released = threading.Event()
        class Cancelled(Exception): pgcode = '57014'
        class Cursor(FakeCursor):
            def execute(self, statement):
                if render(statement).startswith('SELECT *'):
                    entered.set()
                    if not released.wait(3): raise RuntimeError('Cancel was not delivered')
                    raise Cancelled('canceling statement due to user request')
                return super().execute(statement)
        class Connection(FakeConnection):
            def cursor(self): return Cursor(self)
            def cancel(self): released.set()
            def set_session(self, **kwargs): pass
        connection = Connection()
        selection = {'divipola': '08421', 'stamp': '20260930', 'tables': {'R1': '08421_20260930_r1'}}
        worker = RuleWorker({}, 'base', '', '', [('Administrativas', 'regla_1_1', 'SELECT * FROM {esquema_r1}.{tabla_r1}', '')], current_reference=selection, repository_params={'dbname': 'sentencias'})
        from qgis.PyQt.QtCore import Qt
        cancelled = []; worker.cancelled.connect(lambda: cancelled.append(True), Qt.DirectConnection)
        with patch('qgis_control_calidad.current_references.psycopg2.connect', return_value=connection) as connect:
            thread = threading.Thread(target=worker.run); thread.start()
            try:
                self.assertTrue(entered.wait(2)); worker.request_cancel(); thread.join(2)
                self.assertFalse(thread.is_alive())
            finally:
                released.set(); thread.join(4)
        worker.cancel_thread.join(1)
        self.assertEqual(cancelled, [True]); self.assertTrue(connection.closed)
        self.assertEqual(connect.call_count, 1)
