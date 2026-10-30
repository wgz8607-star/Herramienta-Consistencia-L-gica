import sqlite3
import unittest
from unittest.mock import patch
from psycopg2 import sql
from qgis_control_calidad.cica_data import cica_selection, cica_member_predicate
from qgis_control_calidad.territorial_scope import install_scope
from test_temporary_references import render as base_render


def render(value):
    if isinstance(value, sql.Literal):
        return "'" + str(value.wrapped).replace("'", "''") + "'"
    if isinstance(value, sql.Composed):
        return ''.join(render(item) for item in value)
    return base_render(value)


class CicaSelectionTests(unittest.TestCase):
    def test_municipality_and_many_stages_filter_actual_membership(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.create_function('btrim', 1, lambda value: value.strip() if value else value)
        db.execute('CREATE TABLE cica_predio (numero_predial TEXT, etapa TEXT)')
        predios = [('0842101001', 'ASIGNADO'), ('0842101002', 'TRAMITADO'),
                   ('0842101003', 'CONTROL_CALIDAD_GENERAL'), ('1300601001', 'ASIGNADO')]
        db.executemany('INSERT INTO cica_predio VALUES (?,?)', predios)
        db.execute('CREATE TABLE cica_contacto (numero_predial TEXT)')
        db.executemany('INSERT INTO cica_contacto VALUES (?)', [(npn,) for npn, stage in predios] + [('9999901001',)])
        selection = cica_selection('08421', ['ASIGNADO', 'TRAMITADO'])
        query = render(cica_member_predicate('numero_predial', selection, 'main')).replace('::text', '')
        result = [row[0] for row in db.execute('SELECT numero_predial FROM cica_contacto WHERE ' + query)]
        self.assertEqual(result, ['0842101001', '0842101002'])
        all_query = render(cica_member_predicate('numero_predial', cica_selection('', ['ASIGNADO']), 'main')).replace('::text', '')
        self.assertEqual([row[0] for row in db.execute('SELECT numero_predial FROM cica_contacto WHERE ' + all_query)], ['0842101001', '1300601001'])

    def test_invalid_divipola_and_literal_escaping(self):
        with self.assertRaises(ValueError):
            cica_selection('8421', ['ASIGNADO'])
        query = render(cica_member_predicate('numero_predial', cica_selection('08421', ["ETAPA'X"]), 'snc_cica_copy'))
        self.assertIn("'ETAPA''X'", query)

    def test_gdb_views_use_predio_stage_membership_and_r1_only_municipality(self):
        class Database:
            def __init__(self):
                self.statements = []
            def cursor(self): return self
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def execute(self, statement, params=()):
                query = render(statement); self.statements.append(query)
                self.rows = [] if 'information_schema' in query else [('numero_predial',)] if 'pg_attribute' in query else []
            def fetchall(self): return self.rows
        db = Database()
        with patch.object(sql.Identifier, 'as_string', lambda value, connection: render(value)):
            mapping = install_scope(db, 'city', {'cica_predio', 'cica_terreno'}, ['reference_r1'], 'all', cica_filter=cica_selection('08421', ['ASIGNADO']))
        self.assertEqual(len(mapping), 3)
        views = [q for q in db.statements if q.startswith('CREATE TEMP VIEW')]
        terrain = next(q for q in views if 'FROM "pg_temp"."cica_terreno"' in q)
        self.assertIn('"pg_temp".cica_predio', terrain)
        self.assertIn("'ASIGNADO'", terrain)
        reference = next(q for q in views if 'FROM "pg_temp"."reference_r1"' in q)
        self.assertIn("'08421'", reference)
        self.assertNotIn('etapa', reference)

    def test_ui_all_municipalities_and_stage_multiselection(self):
        from qgis.core import QgsApplication
        from qgis.PyQt.QtCore import Qt
        from qgis_control_calidad.ingestion import CicaIngestionDialog
        app = QgsApplication.instance() or QgsApplication([], False)
        dialog = CicaIngestionDialog()
        self.addCleanup(dialog.close)
        dialog.repository_options = [('08421', 'ASIGNADO', 3), ('08421', 'TRAMITADO', 2), ('13006', 'TRAMITADO', 7)]
        dialog.municipality.addItem('Todos', '')
        dialog.municipality.addItem('08421', '08421')
        dialog.municipality.setCurrentIndex(2)
        self.assertEqual(dialog.selected_source_filter(), cica_selection('08421', ['ASIGNADO', 'TRAMITADO']))
        dialog.stages.topLevelItem(1).setCheckState(0, Qt.Unchecked)
        self.assertEqual(dialog.selected_source_filter()['stages'], ('ASIGNADO',))
        dialog.municipality.setCurrentIndex(1)
        self.assertEqual(dialog.selected_source_filter()['municipality'], '')
        self.assertEqual(dialog.stages.topLevelItem(1).text(1), '9')
        dialog.check_stages(False)
        with patch('qgis_control_calidad.ingestion.QMessageBox.warning') as warning:
            dialog.choose_repository()
        warning.assert_called_once()

    def test_repository_download_filters_every_table_before_snapshot(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from qgis_control_calidad.cica_data import TABLES, prepare_repository_cica
        connection = MagicMock(); control = MagicMock(); data = MagicMock()
        control.__enter__.return_value = control; data.__enter__.return_value = data
        control.fetchall.side_effect = [[(table,) for table in TABLES.values()]] + [[('numero_predial',), ('etapa',)] for table in TABLES]
        data.description = [SimpleNamespace(name='numero_predial'), SimpleNamespace(name='etapa')]
        data.fetchmany.return_value = []
        connection.cursor.side_effect = lambda **kwargs: data if kwargs else control
        with patch('psycopg2.connect', return_value=connection):
            prepared = prepare_repository_cica({}, '08421', ('ASIGNADO', 'TRAMITADO'))
        try:
            self.assertEqual(len(prepared), 7)
            self.assertEqual(data.execute.call_count, 7)
            for call in data.execute.call_args_list:
                query = render(call.args[0])
                self.assertIn(' WHERE ', query)
                self.assertIn("'08421%'", query)
                self.assertNotIn('IN (SELECT', query)
                if '"cica_predio"' in query:
                    self.assertIn("'ASIGNADO'", query)
                    self.assertIn("'TRAMITADO'", query)
                else:
                    self.assertNotIn('etapa', query)
        finally:
            for reference in prepared.values(): reference.close()

    def test_stale_selection_cannot_be_applied_without_reading_again(self):
        from qgis.core import QgsApplication
        from qgis.PyQt.QtCore import Qt
        from qgis_control_calidad.ingestion import CicaIngestionDialog
        app = QgsApplication.instance() or QgsApplication([], False)
        dialog = CicaIngestionDialog(); self.addCleanup(dialog.close)
        dialog.source_mode.setCurrentIndex(1)
        dialog.repository_options = [('08421', 'ASIGNADO', 3), ('08421', 'TRAMITADO', 2)]
        dialog.municipality.addItem('08421', '08421')
        dialog.municipality.setCurrentIndex(1)
        dialog.loaded_selection = dialog.selected_source_filter()
        dialog.replace_references = True
        dialog.stages.topLevelItem(0).setCheckState(0, Qt.Unchecked)
        with patch('qgis_control_calidad.ingestion.QMessageBox.warning') as warning:
            dialog.validate_inputs()
        warning.assert_called_once()
        self.assertNotEqual(dialog.result(), dialog.Accepted)

    def test_department_limits_available_municipalities_and_keeps_divipola(self):
        from qgis.core import QgsApplication
        from qgis.PyQt.QtWidgets import QWidget
        from qgis_control_calidad.ingestion import CicaIngestionDialog
        class Owner(QWidget):
            def repository_connection_params(self): return {'dbname': 'sentencias'}
            def report_task(self, function, params):
                return [('08421', 'ASIGNADO', 3), ('08421', 'TRAMITADO', 2), ('13006', 'ASIGNADO', 7)]
        app = QgsApplication.instance() or QgsApplication([], False)
        owner = Owner(); self.addCleanup(owner.close)
        dialog = CicaIngestionDialog(owner); self.addCleanup(dialog.close)
        dialog.load_source_options()
        self.assertGreaterEqual(dialog.municipality.findData(''), 0)
        self.assertIn('ATLÁNTICO', dialog.department.itemText(dialog.department.findData('08')))
        dialog.department.setCurrentIndex(dialog.department.findData('08'))
        self.assertEqual(dialog.municipality.findData('13006'), -1)
        self.assertIn('LURUACO', dialog.municipality.itemText(dialog.municipality.findData('08421')))
        dialog.municipality.setCurrentIndex(dialog.municipality.findData('08421'))
        self.assertEqual(dialog.selected_source_filter()['municipality'], '08421')
        self.assertIn('5 predios', dialog.stage_summary.text())
        dialog.department.setCurrentIndex(dialog.department.findData('13'))
        self.assertEqual(dialog.municipality.findData('08421'), -1)
        self.assertIn('ACHÍ', dialog.municipality.itemText(dialog.municipality.findData('13006')))
        self.assertEqual(dialog.stages.topLevelItemCount(), 0)

    def test_related_tables_use_selected_predios_without_repeating_stage_query(self):
        import csv
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from qgis_control_calidad.cica_data import TABLES, prepare_repository_cica
        connection = MagicMock(); control = MagicMock()
        control.__enter__.return_value = control
        control.fetchall.side_effect = [[(table,) for table in TABLES.values()]] + [[('numero_predial',), ('etapa',)] for _ in TABLES]
        cursors = []
        def cursor_factory(**kwargs):
            if not kwargs: return control
            data = MagicMock(); data.__enter__.return_value = data
            data.description = [SimpleNamespace(name='numero_predial'), SimpleNamespace(name='etapa')]
            rows = [('0842101000001', 'ASIGNADO')]
            if kwargs['name'] != 'snapshot_cica_predio':
                rows += [('0842101000002', 'TRAMITADO')]
            data.fetchmany.side_effect = [rows, []]
            cursors.append((kwargs['name'], data))
            return data
        connection.cursor.side_effect = cursor_factory
        progress = []
        with patch('psycopg2.connect', return_value=connection):
            prepared = prepare_repository_cica({}, '08421', ('ASIGNADO',), progress=progress.append)
        try:
            self.assertEqual(cursors[0][0], 'snapshot_cica_predio')
            self.assertEqual(len(progress), 7)
            for ref in prepared.values():
                self.assertEqual(ref.row_count, 1)
                with ref.csv_path.open() as stream:
                    self.assertEqual(next(csv.reader(stream))[0], '0842101000001')
            queries = [render(cursor.execute.call_args.args[0]) for name, cursor in cursors]
            self.assertEqual(sum('COALESCE(etapa' in query for query in queries), 1)
            self.assertFalse(any('SELECT btrim' in query for query in queries))
        finally:
            for ref in prepared.values(): ref.close()

    def test_timeout_identifies_failed_table_and_discards_partial_copy(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from qgis_control_calidad.cica_data import TABLES, prepare_repository_cica
        class Timeout(Exception):
            pgcode = '57014'
        connection = MagicMock(); control = MagicMock(); data = MagicMock()
        control.__enter__.return_value = control; data.__enter__.return_value = data
        control.fetchall.side_effect = [[(table,) for table in TABLES.values()]] + [[('numero_predial',), ('etapa',)] for _ in TABLES]
        data.description = [SimpleNamespace(name='numero_predial'), SimpleNamespace(name='etapa')]
        data.fetchmany.side_effect = [[('0842101000001', 'ASIGNADO')], [], Timeout('timeout')]
        connection.cursor.side_effect = lambda **kwargs: data if kwargs else control
        closed = []
        from qgis_control_calidad.reference_data import PreparedReference
        original_close = PreparedReference.close
        def record_close(reference):
            closed.append(reference.csv_path)
            original_close(reference)
        with patch('psycopg2.connect', return_value=connection), patch.object(PreparedReference, 'close', record_close):
            with self.assertRaisesRegex(ValueError, 'cica_contacto.*tiempo permitido'):
                prepare_repository_cica({}, '08421', ('ASIGNADO',))
        self.assertEqual(len(closed), 1)
        self.assertFalse(closed[0].exists())
        connection.close.assert_called_once()
