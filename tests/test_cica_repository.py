import csv
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from qgis_control_calidad.cica_data import TABLES, prepare_repository_cica


class RepositoryCicaTests(unittest.TestCase):
    def test_readonly_snapshot_all_tables_including_empty(self):
        connection = MagicMock()
        control = MagicMock()
        control.fetchall.return_value = [(name,) for name in TABLES.values()]
        data = MagicMock()
        data.description = [SimpleNamespace(name='numero_predial'), SimpleNamespace(name='estado')]
        data.fetchmany.side_effect = [[["00001", "ACTIVO"]], []] + [[] for _ in range(6)]
        connection.cursor.side_effect = lambda **kw: data if kw else control
        control.__enter__.return_value = control
        data.__enter__.return_value = data
        with patch('psycopg2.connect', return_value=connection):
            prepared = prepare_repository_cica({'dbname': 'sentencias'})
        try:
            connection.set_session.assert_called_once_with(readonly=True, isolation_level='REPEATABLE READ')
            self.assertEqual(set(prepared), set(TABLES.values()))
            self.assertEqual(sum(ref.row_count for ref in prepared.values()), 1)
            first = next(iter(prepared.values()))
            with first.csv_path.open() as stream:
                self.assertEqual(list(csv.reader(stream))[0][0], '00001')
            self.assertTrue(all('snc_cica_copy' in ref.filename for ref in prepared.values()))
            connection.close.assert_called_once()
        finally:
            for ref in prepared.values():
                ref.close()

    def test_missing_tables_rejected_before_reading(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('cica_predio',)]
        with patch('psycopg2.connect', return_value=connection):
            with self.assertRaisesRegex(ValueError, 'Faltan tablas'):
                prepare_repository_cica({})
        connection.close.assert_called_once()


class CicaSummaryTests(unittest.TestCase):
    def test_status_counts_include_other_states_without_losing_zeroes(self):
        from pathlib import Path
        import tempfile
        from qgis_control_calidad.cica_data import prepare_csv, predio_status_summary
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'predio.csv'
            source.write_text('numero_predial;estado\n0001;ACTIVO\n0002; cancelado \n0003;activo\n0004;OTRO\n0005;\n', encoding='utf-8')
            snapshot = prepare_csv('cica_predio', source)
            try:
                self.assertEqual(predio_status_summary(snapshot), {'active': 2, 'cancelled': 1, 'other': 2})
            finally:
                snapshot.close()

    def test_missing_state_is_unavailable_not_zero(self):
        from qgis_control_calidad.cica_data import predio_status_summary
        self.assertIsNone(predio_status_summary(SimpleNamespace(columns=('numero_predial',))))

    def test_dialog_summary_follows_csv_precedence_and_repository_pending(self):
        import tempfile
        from pathlib import Path
        from qgis.core import QgsApplication
        from qgis_control_calidad.cica_data import prepare_csv
        from qgis_control_calidad.ingestion import CicaIngestionDialog
        app = QgsApplication.instance() or QgsApplication([], False)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'predio.csv'
            source.write_text('numero_predial;estado\n0001;ACTIVO\n', encoding='utf-8')
            snapshot = prepare_csv('cica_predio', source)
            try:
                dialog = CicaIngestionDialog(references={'cica_predio': snapshot})
                self.assertIn('Predios activos: 1', dialog.predio_summary.text())
                self.assertIn('Predios cancelados: 0', dialog.predio_summary.text())
                dialog.source_mode.setCurrentIndex(1)
                self.assertIn('lea las tablas', dialog.predio_summary.text())
                self.assertNotIn('Predios activos: 1', dialog.predio_summary.text())
                dialog.source_mode.setCurrentIndex(0)
                self.assertIn('Predios activos: 1', dialog.predio_summary.text())
                dialog.close()
            finally:
                snapshot.close()


class CicaStagesTests(unittest.TestCase):
    def test_view_read_is_readonly_and_preserves_requested_order(self):
        from qgis_control_calidad.territorial_statistics import read_cica_stages
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        row = ('00123', 'Urbano', '01', 'TRAMITADO', 10, 8, 1, 1)
        cursor.fetchall.return_value = [row]
        with patch('psycopg2.connect', return_value=connection):
            self.assertEqual(read_cica_stages({}), [row])
        connection.set_session.assert_called_once_with(readonly=True)
        from test_temporary_references import render
        query = render(cursor.execute.call_args[0][0])
        self.assertIn('FROM snc_cica_copy.cica_predio', query)
        self.assertNotIn('vw_seguimiento', query)
        self.assertIn("WHEN 'Centro poblado' THEN 2", query)
        self.assertIn("WHEN 'Rural' THEN 3", query)
        connection.close.assert_called_once()

    def test_monitoring_table_is_cica_only_and_keeps_existing_filters(self):
        from qgis.core import QgsApplication
        from qgis_control_calidad.territorial_filter import TerritorialFilterDialog
        app = QgsApplication.instance() or QgsApplication([], False)
        dialog = TerritorialFilterDialog('all', (), lambda: {})
        dialog.set_statistics({'source_statistics': None, 'cica_stages': [
            ('00123', 'Urbano', '01', 'TRAMITADO', 10, 8, 1, 1)]})
        self.assertFalse(dialog.cica_stages.isHidden())
        self.assertEqual(dialog.cica_stages.topLevelItem(0).text(0), '00123')
        self.assertEqual(dialog.cica_stages.topLevelItem(0).text(2), '01')
        self.assertEqual(dialog.cica_stages.topLevelItem(0).text(3), 'TRAMITADO')
        self.assertEqual(dialog.scope.currentData(), 'all')
        dialog.set_statistics({'source_statistics': None, 'cica_stages': [], 'cica_stages_error': 'Sin permiso'})
        self.assertIn('Sin permiso', dialog.cica_stage_note.text())
        self.assertEqual(dialog.cica_stages.topLevelItemCount(), 0)
        dialog.set_statistics({'source_statistics': None})
        self.assertTrue(dialog.cica_stages.isHidden())
        dialog.close()


class RepositoryCicaDateTests(unittest.TestCase):
    def test_reads_latest_timestamp_from_mirror_control(self):
        from datetime import datetime
        from qgis_control_calidad.cica_data import read_repository_cica_date
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('id',), ('fecha_marca',)]
        stamp = datetime(2026, 10, 30, 8, 15)
        cursor.fetchone.return_value = (stamp,)
        with patch('psycopg2.connect', return_value=connection):
            self.assertEqual(read_repository_cica_date({}), stamp)
        connection.set_session.assert_called_once_with(readonly=True)
        self.assertEqual(cursor.execute.call_args_list[1].args[1], ('snc_cica_crudo', '_control'))
        from test_temporary_references import render
        query = render(cursor.execute.call_args[0][0])
        self.assertIn('"snc_cica_crudo"."_control"', query)
        self.assertIn('ORDER BY "fecha_marca" DESC LIMIT 1', query)
        connection.close.assert_called_once()

    def test_missing_date_field_is_explicit(self):
        from qgis_control_calidad.cica_data import read_repository_cica_date
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('id',)]
        with patch('psycopg2.connect', return_value=connection):
            with self.assertRaisesRegex(ValueError, 'fecha_marca'):
                read_repository_cica_date({})
        connection.close.assert_called_once()

    def test_no_record_returns_no_date(self):
        from qgis_control_calidad.cica_data import read_repository_cica_date
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('fecha marca',)]
        cursor.fetchone.return_value = None
        with patch('psycopg2.connect', return_value=connection):
            self.assertIsNone(read_repository_cica_date({}))


class CopySourcePresentationTests(unittest.TestCase):
    def test_copy_hides_csv_rows_and_keeps_gdb_available(self):
        from qgis.core import QgsApplication
        from qgis_control_calidad.ingestion import CicaIngestionDialog
        app = QgsApplication.instance() or QgsApplication([], False)
        dialog = CicaIngestionDialog()
        self.assertEqual(dialog.source_mode.itemText(1), 'Copia base CICA')
        dialog.source_mode.setCurrentIndex(1)
        for label, row in dialog.csv_rows:
            self.assertTrue(label.isHidden())
            self.assertTrue(row.isHidden())
        self.assertFalse(dialog.gdb.isHidden())
        dialog.source_mode.setCurrentIndex(0)
        for label, row in dialog.csv_rows:
            self.assertFalse(label.isHidden())
            self.assertFalse(row.isHidden())
        dialog.close()

    def test_copy_label_shows_date_and_time(self):
        from datetime import datetime
        from qgis.core import QgsApplication
        from qgis.PyQt.QtWidgets import QWidget
        from qgis_control_calidad.ingestion import CicaIngestionDialog
        class Owner(QWidget):
            def repository_connection_params(self):
                return {'dbname': 'sentencias'}
            def report_task(self, function, params):
                return datetime(2026, 10, 30, 8, 15, 2)
        app = QgsApplication.instance() or QgsApplication([], False)
        owner = Owner()
        dialog = CicaIngestionDialog(owner)
        dialog.source_mode.setCurrentIndex(1)
        self.assertEqual(dialog.repository_date.text(), 'Copia base CICA — 30/10/2026 · 08:15:02')
        dialog.close();owner.close()


class DirectMonitoringTests(unittest.TestCase):
    def test_direct_table_query_keeps_selected_municipality(self):
        from qgis_control_calidad.territorial_statistics import read_cica_stages
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        with patch('psycopg2.connect', return_value=connection):
            data = read_cica_stages({}, '08421', include_source=True)
        self.assertEqual(data, {'source': 'sentencias.snc_cica_copy.cica_predio', 'rows': []})
        self.assertIn('FROM snc_cica_copy.cica_predio', cursor.execute.call_args.args[0])
        self.assertNotIn('vw_seguimiento', cursor.execute.call_args.args[0])
        self.assertEqual(cursor.execute.call_args.args[1], ('08421%',))

    def test_file_statistics_preserve_cp_codes_stage_and_states(self):
        import tempfile
        from pathlib import Path
        from qgis_control_calidad.cica_data import prepare_csv
        from qgis_control_calidad.territorial_statistics import cica_stages_from_snapshot
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'predio.csv'
            source.write_text('numero_predial;estado;etapa\n0842101000001;ACTIVO;TRAMITADO\n0842102000001;CANCELADO;ASIGNADO\n0842102000002;ACTIVO;ASIGNADO\n0842100000001;OTRO;\n')
            ref = prepare_csv('cica_predio', source)
            try:
                data = cica_stages_from_snapshot(ref)
                self.assertEqual(data['rows'], [
                    ('08421', 'Urbano', '01', 'TRAMITADO', 1, 1, 0, 0),
                    ('08421', 'Centro poblado', '02', 'ASIGNADO', 2, 1, 1, 0),
                    ('08421', 'Rural', '00', '', 1, 0, 0, 1)])
            finally:
                ref.close()

    def test_direct_query_aggregates_actual_predios_by_cp_stage_and_state(self):
        import sqlite3
        from qgis_control_calidad.territorial_statistics import read_cica_stages
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []
        with patch('psycopg2.connect', return_value=connection):
            read_cica_stages({}, '08421')
        query, args = cursor.execute.call_args.args
        query = query.replace('::text', '').replace(' ~ ', ' REGEXP ').replace('%s', '?')
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.create_function('btrim', 1, lambda value: value.strip() if value else value)
        db.create_function('regexp', 2, lambda pattern, value: bool(__import__('re').search(pattern, value or '')))
        db.execute("ATTACH DATABASE ':memory:' AS snc_cica_copy")
        db.execute('CREATE TABLE snc_cica_copy.cica_predio (numero_predial TEXT, estado TEXT, etapa TEXT)')
        db.executemany('INSERT INTO snc_cica_copy.cica_predio VALUES (?,?,?)', [
            ('0842101000001', 'ACTIVO', 'TRAMITADO'),
            ('0842102000001', 'CANCELADO', 'ASIGNADO'),
            ('0842102000002', 'ACTIVO', 'ASIGNADO'),
            ('0842100000001', 'OTRO', None),
            ('1300601000001', 'ACTIVO', 'ASIGNADO')])
        self.assertEqual(db.execute(query, args).fetchall(), [
            ('08421', 'Urbano', '01', 'TRAMITADO', 1, 1, 0, 0),
            ('08421', 'Centro poblado', '02', 'ASIGNADO', 2, 1, 1, 0),
            ('08421', 'Rural', '00', '', 1, 0, 0, 1)])
