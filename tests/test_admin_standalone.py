import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from cargador_reglas import servicio
from cargador_reglas.repositorio import RuleUpload, create_template, make_plan
from test_rule_upload import RepositoryConnection, TABLE, values


class StandaloneServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'reglas.xlsx'
        create_template(self.path, [values()])

    def test_changed_excel_blocks_load_before_connecting(self):
        connection = RepositoryConnection()
        with patch.object(servicio.psycopg2, 'connect', return_value=connection):
            plan = servicio.inspect_file({}, TABLE, self.path)
        create_template(self.path, [values('002')])
        with patch.object(servicio.psycopg2, 'connect') as connect:
            with self.assertRaisesRegex(ValueError, 'cambió después'):
                servicio.apply_plan({}, plan)
        connect.assert_not_called()

    def test_connection_credentials_are_only_passed_to_the_driver(self):
        connection = RepositoryConnection()
        params = {'host': 'servidor', 'dbname': 'sentencias', 'user': 'administrador', 'password': 'ejemplo_solo_prueba'}
        with patch.object(servicio.psycopg2, 'connect', return_value=connection) as connect:
            plan = servicio.inspect_file(params, TABLE, self.path)
        self.assertEqual(connect.call_args.kwargs['password'], params['password'])
        self.assertNotIn(params['password'], repr(plan))
        self.assertEqual(connection.records, [])
        self.assertTrue(connection.closed)


@unittest.skipUnless(os.environ.get('DISPLAY'), 'Requiere un servidor gráfico para comprobar Tkinter.')
class StandaloneGuiTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from cargador_reglas.interfaz import AdministratorApp
        self.root = tk.Tk(); self.root.withdraw()
        self.app = AdministratorApp(self.root)
        self.addCleanup(self.cleanup)
        self.app.user.set('administrador')

    def cleanup(self):
        if self.root.winfo_exists():
            self.app.close()

    def plan(self):
        return make_plan(TABLE, [RuleUpload(2, values())], [])

    def pump(self):
        limit = time.monotonic() + 3
        while self.app.busy and time.monotonic() < limit:
            self.root.update()
            time.sleep(0.005)
        self.assertFalse(self.app.busy)

    def test_preview_enables_load_and_destination_change_invalidates_it(self):
        self.app.show_plan(self.plan())
        self.assertEqual(str(self.app.apply_button['state']), 'normal')
        self.assertEqual(self.app.sql_text.get('1.0', 'end').strip(), values()[4])
        self.app.destination.set('public.reglas_cargue_snc_xtf')
        self.assertIsNone(self.app.plan)
        self.assertEqual(str(self.app.apply_button['state']), 'disabled')

    def test_cancelling_confirmation_never_calls_database(self):
        self.app.show_plan(self.plan())
        with patch('cargador_reglas.interfaz.messagebox.askyesno', return_value=False), patch.object(servicio, 'apply_plan') as apply:
            self.app.apply()
        apply.assert_not_called()

    def test_background_work_keeps_ui_events_running(self):
        release = threading.Event(); results = []
        self.root.after(20, release.set)
        self.app.run_task(lambda: release.wait(1), results.append)
        self.pump()
        self.assertEqual(results, [True])

    def test_errors_restore_controls_and_hide_the_password(self):
        self.app.password.set('ejemplo_solo_prueba')
        def fail():
            raise RuntimeError('Fallo con ejemplo_solo_prueba')
        with patch('cargador_reglas.interfaz.messagebox.showerror') as message:
            self.app.run_task(fail, lambda result: None)
            self.pump()
        self.assertNotIn('ejemplo_solo_prueba', repr(message.call_args))
        self.assertNotIn('ejemplo_solo_prueba', self.app.activity.get('1.0', 'end'))
        self.assertTrue(all(str(widget['state']) != 'disabled' for widget, _ in self.app.widgets if widget is not self.app.apply_button))
        self.assertEqual(str(self.app.apply_button['state']), 'disabled')
