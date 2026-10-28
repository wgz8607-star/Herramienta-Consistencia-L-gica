import os
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from qgis.core import QgsApplication, QgsDataSourceUri
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QMessageBox
from administrador_reglas_qgis import conexiones, servicio
from administrador_reglas_qgis.dialog import AdministratorDialog
from administrador_reglas_qgis.repositorio import RuleUpload, create_template, make_plan, insert_import
from administrador_reglas_qgis.plugin import AdministradorReglasPlugin
from test_rule_upload import RepositoryConnection, values, render

app = QgsApplication.instance() or QgsApplication([], False)
app.initQgis()


class AdminQgisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'reglas.xlsx'
        create_template(self.path, [values()])
        self.widget = AdministratorDialog()
        self.addCleanup(self.widget.close)
        self.widget.mode.setCurrentIndex(1)
        self.widget.host.setText('servidor_prueba'); self.widget.user.setText('administrador')

    def target(self, insert=True):
        self.widget.schema.blockSignals(True); self.widget.schema.addItem('revision'); self.widget.schema.blockSignals(False)
        self.widget.table.addItem('mis_reglas', {'name': 'mis_reglas', 'insert': insert})
        return make_plan('mis_reglas', [RuleUpload(2, values())], [], schema='revision', catalog_target=True)

    def pump(self):
        limit = time.monotonic() + 3
        while self.widget.busy and time.monotonic() < limit:
            app.processEvents(); time.sleep(0.005)
        app.processEvents()
        self.assertFalse(self.widget.busy)

    def test_saved_qgis_connection_uses_native_uri_credentials_and_ssl(self):
        uri = QgsDataSourceUri(); uri.setConnection('host_prueba', '5432', 'base_prueba', 'usuario_prueba', 'password_solo_prueba', QgsDataSourceUri.SslRequire)
        with patch.object(conexiones, 'provider_connections', return_value={'Conexión': SimpleNamespace(uri=lambda: uri.uri(False))}):
            params = conexiones.saved_connection_params('Conexión')
        self.assertEqual(params['host'], 'host_prueba'); self.assertEqual(params['dbname'], 'base_prueba')
        self.assertEqual(params['user'], 'usuario_prueba'); self.assertEqual(params['password'], 'password_solo_prueba')
        self.assertEqual(params['sslmode'], 'require')

    def test_saved_service_uri_is_supported(self):
        uri = QgsDataSourceUri(); uri.setConnection('servicio_prueba', 'sentencias', '', '', QgsDataSourceUri.SslPrefer)
        with patch.object(conexiones, 'provider_connections', return_value={'Servicio': SimpleNamespace(uri=lambda: uri.uri(False))}):
            params = conexiones.saved_connection_params('Servicio')
        self.assertEqual(params['service'], 'servicio_prueba')

    def test_authentication_failure_does_not_fall_back_to_other_credentials(self):
        uri = QgsDataSourceUri(); uri.setConnection('host', '5432', 'sentencias', '', '', QgsDataSourceUri.SslPrefer, 'abc1234')
        manager = MagicMock(); manager.loadAuthenticationConfig.return_value = False
        with patch.object(conexiones, 'provider_connections', return_value={'Protegida': SimpleNamespace(uri=lambda: uri.uri(False))}), patch.object(conexiones.QgsApplication, 'authManager', return_value=manager):
            with self.assertRaisesRegex(ValueError, 'autenticación'):
                conexiones.saved_connection_params('Protegida')

    def test_manual_connection_parameters_have_no_embedded_password(self):
        params = self.widget.params()
        self.assertEqual(params['host'], 'servidor_prueba')
        self.assertEqual(params['password'], '')
        self.widget.port.setText('incorrecto')
        with self.assertRaisesRegex(ValueError, 'puerto'):
            self.widget.params()

    def test_catalog_is_read_only_and_lists_only_compatible_tables(self):
        connection = RepositoryConnection([('mis_reglas', True), ('solo_lectura', False)])
        with patch.object(servicio.psycopg2, 'connect', return_value=connection):
            result = servicio.list_tables({}, 'revision')
        self.assertEqual(result, [('mis_reglas', True), ('solo_lectura', False)])
        self.assertIn({'readonly': True}, connection.events)
        query = next(value for value in connection.events if isinstance(value, str) and value.startswith('SELECT'))
        self.assertIn('COUNT(DISTINCT c.column_name)', query)
        self.assertIn('information_schema.columns', query)
        self.assertTrue(connection.closed)

    def test_schema_listing_filters_system_names_and_respects_usage(self):
        connection = RepositoryConnection([('public',), ('revision',)])
        with patch.object(servicio.psycopg2, 'connect', return_value=connection):
            self.assertEqual(servicio.list_schemas({}), ['public', 'revision'])
        query = next(value for value in connection.events if isinstance(value, str) and value.startswith('SELECT'))
        self.assertIn('has_schema_privilege', query)
        self.assertIn('information_schema', query)

    def test_custom_schema_load_writes_only_the_selected_table(self):
        plan = self.target()
        connection = RepositoryConnection()
        with connection:
            self.assertEqual(insert_import(connection, plan), 1)
        insert = next(query for query in connection.events if isinstance(query, str) and query.startswith('INSERT'))
        self.assertIn('"revision"."mis_reglas"', insert)
        self.assertNotIn('public.', insert)
        self.assertEqual(len(connection.records), 1)

    def test_schema_and_table_names_are_quoted_as_identifiers(self):
        plan = make_plan('tabla "especial"', [RuleUpload(2, values())], [], schema='esquema con espacio', catalog_target=True)
        connection = RepositoryConnection()
        with connection:
            insert_import(connection, plan)
        insert = next(query for query in connection.events if isinstance(query, str) and query.startswith('INSERT'))
        self.assertIn('"esquema con espacio"."tabla ""especial"""', insert)

    def test_changed_connection_after_preview_blocks_write(self):
        connection = RepositoryConnection()
        with patch.object(servicio.psycopg2, 'connect', return_value=connection):
            plan = servicio.inspect_file({'dbname': 'uno'}, 'mis_reglas', self.path, 'revision')
        with patch.object(servicio.psycopg2, 'connect') as connect:
            with self.assertRaisesRegex(ValueError, 'conexión cambió'):
                servicio.apply_plan({'dbname': 'otro'}, plan)
        connect.assert_not_called()

    def test_read_only_target_does_not_enable_load(self):
        plan = self.target(insert=False); self.widget.show_plan(plan)
        self.assertTrue(self.widget.preview_button.isEnabled())
        self.assertTrue(self.widget.export_button.isEnabled())
        self.assertFalse(self.widget.load_button.isEnabled())
        with patch.object(servicio, 'apply_plan') as apply:
            self.widget.apply()
        apply.assert_not_called()

    def test_destination_and_connection_changes_invalidate_preview(self):
        plan = self.target(); self.widget.show_plan(plan)
        self.assertTrue(self.widget.load_button.isEnabled())
        self.widget.host.setText('otro_servidor')
        self.assertIsNone(self.widget.plan); self.assertFalse(self.widget.load_button.isEnabled())
        self.assertEqual(self.widget.schema.count(), 0)

    def test_cancelled_confirmation_never_starts_write(self):
        plan = self.target(); self.widget.show_plan(plan)
        with patch.object(QMessageBox, 'exec_', return_value=QMessageBox.Cancel), patch.object(servicio, 'apply_plan') as apply:
            self.widget.apply()
        apply.assert_not_called()
        self.assertIsNotNone(self.widget.plan)

    def test_worker_keeps_ui_events_alive_and_restores_controls(self):
        release = threading.Event(); results = []
        QTimer.singleShot(20, release.set)
        self.widget.start_task(lambda: release.wait(1), (), results.append)
        self.pump()
        self.assertEqual(results, [True]); self.assertTrue(self.widget.connection_box.isEnabled())

    def test_schema_to_table_loading_is_sequential(self):
        with patch.object(servicio, 'list_schemas', return_value=['public', 'revision']), patch.object(servicio, 'list_tables', return_value=[('mis_reglas', True)]) as tables:
            self.widget.load_schemas(); self.pump()
        tables.assert_called_once()
        self.assertEqual(self.widget.schema.currentText(), 'public')
        self.assertEqual(self.widget.table.currentData()['name'], 'mis_reglas')

    def test_plugin_can_initialize_without_the_validator(self):
        iface = MagicMock(); iface.mainWindow.return_value = None
        plugin = AdministradorReglasPlugin(iface); plugin.initGui()
        iface.addPluginToDatabaseMenu.assert_called_once()
        plugin.open_dialog()
        self.assertIsInstance(plugin.dialog, AdministratorDialog)
        plugin.unload()
        self.assertIsNone(plugin.dialog)

    def test_plugin_backend_is_bundled_and_matches_shared_source(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual((root/'administrador_reglas_qgis/repositorio.py').read_bytes(), (root/'cargador_reglas/repositorio.py').read_bytes())
