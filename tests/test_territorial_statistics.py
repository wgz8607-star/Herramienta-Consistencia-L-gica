import csv
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from qgis.PyQt.QtCore import Qt
from qgis_control_calidad.territorial_statistics import statistics_from_values, included_count, prefix_counts, read_source_statistics
from qgis_control_calidad.territorial_filter import TerritorialFilterDialog, ScopeSelector
from qgis_control_calidad.territorial_scope import predicate, SCOPES
from test_temporary_references import render, app

URBAN = '08421010000010001'
RURAL = '08421000000010001'
CENTER = '08421020000010001'


class TerritorialStatisticsTests(unittest.TestCase):
    def data(self):
        return statistics_from_values([URBAN + '0' * 13, URBAN + '0' * 13, RURAL + '0' * 13,
                                       CENTER + '0' * 13, None, '0842101short'], 'Ejemplo')

    def test_counts_include_duplicates_unclassified_and_missing_prefixes(self):
        data = self.data()
        self.assertEqual(data['total'], 6)
        self.assertEqual(data['totals'], {'urban': 3, 'rural': 1, 'center': 1, 'unknown': 1})
        self.assertEqual(prefix_counts(data), {URBAN: 2, RURAL: 1, CENTER: 1})
        self.assertEqual(included_count(data, 'all'), 6)
        self.assertEqual(included_count(data, 'urban+rural'), 4)
        self.assertEqual(included_count(data, 'urban+center'), 4)
        self.assertEqual(included_count(data, 'rural+center'), 2)
        self.assertEqual(included_count(data, 'all', (URBAN,)), 2)
        self.assertEqual(included_count(data, 'rural', (URBAN,)), 0)

    def test_combo_predicates_match_statistics_and_single_scopes(self):
        import sqlite3
        db = sqlite3.connect(':memory:'); self.addCleanup(db.close)
        db.create_function('btrim', 1, lambda v: v.strip() if v else v)
        db.create_function('regexp', 2, lambda pattern, value: bool(__import__('re').search(pattern, value or '')))
        values = [URBAN, URBAN, RURAL, CENTER, None, '0842101short']
        db.execute('CREATE TABLE predios (npn TEXT)')
        db.executemany('INSERT INTO predios VALUES (?)', [(value,) for value in values])
        for scope in SCOPES:
            query = render(predicate('npn', scope)).replace('::text', '').replace(' ~ ', ' REGEXP ')
            count = db.execute('SELECT COUNT(*) FROM predios WHERE ' + query).fetchone()[0]
            self.assertEqual(count, included_count(self.data(), scope), scope)

    def test_temporary_statistics_do_not_connect_or_lose_leading_zeroes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'predios.csv'
            with path.open('w', newline='') as output:
                csv.writer(output).writerows([[URBAN + '0' * 13], [URBAN + '0' * 13], ['']])
            snapshot = SimpleNamespace(columns=('numero_predial',), csv_path=path)
            with patch('qgis_control_calidad.territorial_statistics.psycopg2.connect') as connect:
                data = read_source_statistics({}, '', 'CICA', snapshot)
            connect.assert_not_called()
            self.assertEqual(data['total'], 3)
            self.assertEqual(prefix_counts(data)[URBAN], 2)

    def test_database_aggregates_readonly_and_closes_for_both_models(self):
        class Database:
            def __init__(self): self.queries = []; self.closed = False
            def set_session(self, **kwargs): self.options = kwargs
            def cursor(self): return self
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def execute(self, statement, params=()):
                self.queries.append((render(statement), params))
            def fetchall(self):
                return [('numero_predial_nacional',)] if 'information_schema.columns' in self.queries[-1][0] else [(URBAN, 2), (None, 1)]
            def close(self): self.closed = True
        for model, table in [('CICA', 'cica_predio'), ('Modelo Interno de Levantamiento 1.0', 'ilc_predio')]:
            db = Database()
            with patch('qgis_control_calidad.territorial_statistics.psycopg2.connect', return_value=db):
                data = read_source_statistics({}, 'fuente', model)
            self.assertEqual(data['total'], 3)
            self.assertTrue(db.closed)
            self.assertEqual(db.options, {'readonly': True})
            self.assertIn('"fuente"."' + table + '"', db.queries[-1][0])
            self.assertIn('COUNT(*)', db.queries[-1][0])
            self.assertIn('GROUP BY 1', db.queries[-1][0])

    def test_checkbox_selector_handles_combinations_all_and_empty(self):
        selector = ScopeSelector('urban+rural')
        self.addCleanup(selector.close)
        self.assertEqual(selector.currentData(), 'urban+rural')
        selector.checks['rural'].setChecked(False)
        self.assertEqual(selector.currentData(), 'urban')
        selector.checks['center'].setChecked(True)
        self.assertEqual(selector.currentData(), 'urban+center')
        selector.checks['all'].setChecked(True)
        self.assertEqual(selector.currentData(), 'all')
        selector.checks['all'].setChecked(False)
        self.assertIsNone(selector.currentData())

    def test_dialog_updates_count_and_bulk_selection_respects_hidden_codes(self):
        dialog = TerritorialFilterDialog('all', (), lambda: {'source_statistics': self.data(), 'r1_statistics': self.data()})
        self.addCleanup(dialog.close)
        dialog.load_codes()
        self.assertIn('6 de 6', dialog.selection_statistics.text())
        dialog.scope.set_scope('urban+rural')
        self.assertIn('4 de 6', dialog.selection_statistics.text())
        dialog.search.setText(URBAN)
        dialog.select_all_button.click()
        self.assertEqual(dialog.selected_prefixes(), (URBAN,))
        self.assertIn('2 de 6', dialog.selection_statistics.text())
        dialog.search.setText(RURAL)
        dialog.select_all_button.click()
        self.assertEqual(dialog.selected_prefixes(), tuple(sorted((URBAN, RURAL))))
        dialog.deselect_all_button.click()
        self.assertEqual(dialog.selected_prefixes(), (URBAN,))
        dialog.search.clear()
        dialog.deselect_all_button.click()
        self.assertEqual(dialog.selected_prefixes(), ())
        self.assertIn('4 de 6', dialog.selection_statistics.text())

    def test_empty_scope_and_incompatible_prefixes_cannot_apply(self):
        dialog = TerritorialFilterDialog('rural', (URBAN,), self.data)
        self.addCleanup(dialog.close)
        with patch('qgis_control_calidad.territorial_filter.QMessageBox.warning') as warning:
            dialog.accept()
            warning.assert_called_once()
        self.assertEqual(dialog.result(), 0)
        dialog.scope.checks['rural'].setChecked(False)
        with patch('qgis_control_calidad.territorial_filter.QMessageBox.warning') as warning:
            dialog.accept()
            warning.assert_called_once()

    def test_refresh_failure_does_not_reuse_old_statistics(self):
        dialog = TerritorialFilterDialog('all', (), lambda: {'source_statistics': self.data(), 'r1_statistics': self.data()})
        self.addCleanup(dialog.close)
        dialog.load_codes()
        dialog.loader = lambda: (_ for _ in ()).throw(RuntimeError('Sin conexión'))
        with patch('qgis_control_calidad.territorial_filter.QMessageBox.warning'):
            dialog.load_codes()
        self.assertIsNone(dialog.statistics)
        self.assertIn('no disponibles', dialog.selection_statistics.text())
        self.assertFalse(dialog.reading)
        self.assertTrue(dialog.read_button.isEnabled())

    def test_r1_counts_are_separate_and_follow_the_same_selection(self):
        from qgis_control_calidad.territorial_statistics import read_filter_statistics
        with tempfile.TemporaryDirectory() as directory:
            def snapshot(name, values):
                path = Path(directory) / name
                with path.open('w', newline='') as output:
                    csv.writer(output).writerows([[value] for value in values])
                return SimpleNamespace(columns=('numero_predial',), csv_path=path, filename=name)
            source = snapshot('cica.csv', [URBAN, RURAL])
            r1 = snapshot('r1.csv', [URBAN, URBAN, CENTER])
            data = read_filter_statistics({}, '', 'CICA', source, r1)
            self.assertEqual(data['source_statistics']['total'], 2)
            self.assertEqual(data['r1_statistics']['total'], 2)
            dialog = TerritorialFilterDialog('urban+rural', (), lambda: data)
            self.addCleanup(dialog.close); dialog.load_codes()
            self.assertIn('Base catastral a validar (registros): 2 de 2', dialog.selection_statistics.text())
            self.assertEqual(dialog.overview.rows['total'].text(2), '2')
            self.assertEqual(dialog.codes.columnCount(), 4)
            self.assertIn('R1 (predios únicos): 1 de 2', dialog.selection_statistics.text())
            dialog.search.setText(URBAN); dialog.select_all_button.click()
            self.assertIn('R1 (predios únicos): 1 de 2', dialog.selection_statistics.text())
            row = next(item for item in dialog.items() if item.data(0, Qt.UserRole) == URBAN)
            self.assertEqual(row.text(3), '1')
            # R1-only codes remain visible under the appropriate scope, source count zero.
            dialog.scope.set_scope('all'); dialog.search.clear()
            row = next(item for item in dialog.items() if item.data(0, Qt.UserRole) == CENTER)
            self.assertEqual(row.text(3), '1')

    def test_missing_r1_is_not_reported_as_zero_and_source_errors_are_independent(self):
        from qgis_control_calidad.territorial_statistics import read_filter_statistics
        with patch('qgis_control_calidad.territorial_statistics.read_source_statistics', return_value=self.data()):
            data = read_filter_statistics({}, 'city', 'CICA')
        self.assertIsNone(data['r1_statistics'])
        self.assertIn('no cargado', data['r1_status'])
        r1 = SimpleNamespace(filename='r1.xlsx')
        with patch('qgis_control_calidad.territorial_statistics.read_source_statistics', side_effect=[RuntimeError('Fuente falló'), self.data()]):
            data = read_filter_statistics({}, 'city', 'CICA', r1_snapshot=r1)
        self.assertIsNone(data['source_statistics'])
        self.assertEqual(data['r1_statistics']['total'], 6)
        self.assertIn('Fuente falló', data['source_error'])

    def test_current_r1_uses_selected_table_and_date_and_preserves_source_on_error(self):
        from qgis_control_calidad.territorial_statistics import read_filter_statistics
        selected = {'divipola': '08421', 'stamp': '20260930', 'date': '2026-09-30', 'tables': {'R1': '08421_20260930_r1'}}
        with patch('qgis_control_calidad.territorial_statistics.read_source_statistics', side_effect=[self.data(), self.data()]) as read:
            data = read_filter_statistics({}, 'city', 'CICA', reference_mode='current', current_reference=selected, repository_params={'dbname': 'repositorio'})
        self.assertEqual(read.call_args.args[:3], ({'dbname': 'repositorio'}, 'r1_r2', 'R1'))
        self.assertEqual(read.call_args.kwargs['table_name'], '08421_20260930_r1')
        self.assertIn('2026-09-30', data['r1_statistics']['source'])
        with patch('qgis_control_calidad.territorial_statistics.read_source_statistics', side_effect=[self.data(), RuntimeError('Sin permiso')]):
            data = read_filter_statistics({}, 'city', 'CICA', reference_mode='current', current_reference=selected, repository_params={})
        self.assertEqual(data['source_statistics']['total'], 6)
        self.assertIsNone(data['r1_statistics'])
        self.assertIn('Sin permiso', data['r1_status'])

    def test_unique_r1_counts_full_npns_not_territorial_prefixes(self):
        first = URBAN + '0000000000001'
        second = URBAN + '0000000000002'
        data = statistics_from_values([first, first, ' ' + first + ' ', second, None, '', '  '], unique=True)
        self.assertEqual(data['total'], 2)
        self.assertEqual(prefix_counts(data), {URBAN: 2})
        self.assertEqual(data['row_count'], 7)
        self.assertEqual(data['duplicates'], 2)
        self.assertEqual(data['missing_npn'], 3)
        self.assertEqual(included_count(data, 'urban', (URBAN,)), 2)

    def test_current_r1_uses_distinct_complete_npn_and_excludes_missing_values(self):
        class Database:
            def __init__(self): self.queries = []; self.closed = False
            def set_session(self, **kwargs): self.options = kwargs
            def cursor(self): return self
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def execute(self, statement, params=()): self.queries.append(render(statement))
            def fetchall(self):
                return [('numero_predial',)] if 'information_schema.columns' in self.queries[-1] else [(URBAN, 2, 5, 5), ('', 0, 2, 0)]
            def close(self): self.closed = True
        db = Database()
        with patch('qgis_control_calidad.territorial_statistics.psycopg2.connect', return_value=db):
            data = read_source_statistics({}, 'r1_r2', 'R1', table_name='08421_20260930_r1')
        self.assertIn('COUNT(DISTINCT NULLIF(btrim("numero_predial"::text)', db.queries[-1])
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['duplicates'], 3)
        self.assertEqual(data['missing_npn'], 2)
        self.assertEqual(prefix_counts(data), {URBAN: 2})
        self.assertEqual(db.options, {'readonly': True})
        self.assertTrue(db.closed)

    def test_embedded_filter_applies_without_closing_or_opening_a_dialog(self):
        from qgis.PyQt.QtWidgets import QWidget
        parent = QWidget(); self.addCleanup(parent.close)
        editor = TerritorialFilterDialog('urban+rural', (), lambda: [], parent, embedded=True)
        self.addCleanup(editor.close)
        applied = []; editor.filterApplied.connect(lambda scope, prefixes: applied.append((scope, prefixes)))
        editor.accept()
        self.assertEqual(applied, [('urban+rural', ())])
        self.assertEqual(editor.result(), 0)
        self.assertFalse(editor.isWindow())
        self.assertEqual(editor.codes.columnCount(), 4)

    def test_filter_tab_requires_both_sources_and_resets_on_source_change(self):
        from qgis_control_calidad.dialog import ControlCalidadDialog
        widget = ControlCalidadDialog(); self.addCleanup(widget.close)
        index = widget.advanced_filter_tab_index
        self.assertEqual([widget.left_tabs.tabText(i) for i in range(3)], ['Conexión', 'Referencias R1/R2', 'Estadística y filtro avanzado'])
        self.assertFalse(widget.left_tabs.isTabEnabled(index))
        self.assertFalse(widget.schema_controls.isAncestorOf(widget.filter_overview))
        widget.schema.addItem('city')
        self.assertFalse(widget.left_tabs.isTabEnabled(index))
        widget.temporary_references['R1'] = SimpleNamespace(close=lambda: None)
        widget.update_advanced_filter_availability()
        self.assertTrue(widget.left_tabs.isTabEnabled(index))
        widget.scope_prefixes = (URBAN,)
        widget.filter_statistics = {'r1_statistics': self.data()}
        widget.temporary_references['R1'] = SimpleNamespace(close=lambda: None)
        widget.update_advanced_filter_availability()
        self.assertEqual(widget.scope_prefixes, ())
        self.assertIsNone(widget.filter_statistics)
        widget.schema.clear()
        self.assertFalse(widget.left_tabs.isTabEnabled(index))
        widget.model.setCurrentText('CICA')
        widget.cica_references['cica_predio'] = SimpleNamespace(close=lambda: None)
        widget.update_advanced_filter_availability()
        self.assertTrue(widget.left_tabs.isTabEnabled(index))
        widget.release_references()
        self.assertFalse(widget.left_tabs.isTabEnabled(index))

    def test_current_r1_tab_remains_disabled_for_missing_r1_or_typed_municipality(self):
        from qgis_control_calidad.dialog import ControlCalidadDialog
        widget = ControlCalidadDialog(); self.addCleanup(widget.close)
        widget.schema.addItem('city')
        with patch.object(widget, 'load_current_references'):
            widget.reference_mode.setCurrentIndex(1)
        selection = {'divipola': '08421', 'date': '2026-09-30', 'tables': {'R2': '08421_20260930_r2'}}
        widget.municipality.addItem('08421', selection)
        self.assertFalse(widget.left_tabs.isTabEnabled(widget.advanced_filter_tab_index))
        selection['tables']['R1'] = '08421_20260930_r1'
        widget.municipality.setItemData(widget.municipality.currentIndex(), selection)
        widget.show_current_reference()
        self.assertTrue(widget.left_tabs.isTabEnabled(widget.advanced_filter_tab_index))
        widget.municipality.setEditText('Municipio sin seleccionar')
        self.assertFalse(widget.left_tabs.isTabEnabled(widget.advanced_filter_tab_index))

    def test_compact_overview_shows_both_sources_without_combining_counts(self):
        from qgis_control_calidad.territorial_filter import TerritorialOverview
        view = TerritorialOverview(); self.addCleanup(view.close)
        source = self.data()
        r1 = statistics_from_values([URBAN, URBAN, RURAL], unique=True, source='R1 ejemplo')
        view.set_statistics({'source_statistics': source, 'r1_statistics': r1})
        self.assertEqual((view.rows['total'].text(1), view.rows['total'].text(2)), ('6', '2'))
        self.assertEqual((view.rows['urban'].text(1), view.rows['urban'].text(2)), ('3', '1'))
        self.assertIn('1 duplicados', view.r1_note.text())
        view.set_statistics({'source_error': 'Sin conexión', 'r1_statistics': r1})
        self.assertEqual((view.rows['total'].text(1), view.rows['total'].text(2)), ('—', '2'))
        self.assertIn('Sin conexión', view.source_label.text())

    def test_popup_cancel_preserves_applied_filter_and_accept_updates_it(self):
        from qgis_control_calidad.dialog import ControlCalidadDialog
        from qgis.PyQt.QtWidgets import QDialog
        from unittest.mock import MagicMock
        widget = ControlCalidadDialog(); self.addCleanup(widget.close)
        widget.schema.addItem('city')
        widget.temporary_references['R1'] = SimpleNamespace(close=lambda: None)
        widget.update_advanced_filter_availability()
        widget.filter_statistics = {'source_statistics': self.data(), 'r1_statistics': self.data()}
        widget.apply_advanced_filter('rural', ())
        popup = MagicMock()
        popup.scope.currentData.return_value = 'urban+rural'
        popup.selected_prefixes.return_value = (URBAN,)
        popup.exec_.return_value = QDialog.Rejected
        with patch('qgis_control_calidad.dialog.TerritorialFilterDialog', return_value=popup):
            widget.open_advanced_filter_window()
        self.assertEqual((widget.scope_selection, widget.scope_prefixes), ('rural', ()))
        popup.set_statistics.assert_called_once()
        popup.exec_.return_value = QDialog.Accepted
        with patch('qgis_control_calidad.dialog.TerritorialFilterDialog', return_value=popup):
            widget.open_advanced_filter_window()
        self.assertEqual((widget.scope_selection, widget.scope_prefixes), ('urban+rural', (URBAN,)))
        self.assertFalse(hasattr(widget, 'filter_editor'))

    def test_cica_status_counts_and_requested_summary_text(self):
        from qgis_control_calidad.territorial_filter import TerritorialOverview
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'predios.csv'
            with path.open('w', newline='') as output:
                csv.writer(output).writerows([[URBAN, 'ACTIVO'], [RURAL, ' cancelado '], [CENTER, 'Activo'], [CENTER, None]])
            data = read_source_statistics({}, '', 'CICA', SimpleNamespace(columns=('numero_predial', 'estado'), csv_path=path))
        self.assertEqual(data['status_counts']['active'], 2)
        self.assertEqual(data['status_counts']['cancelled'], 1)
        self.assertEqual(data['status_counts']['other'], 1)
        r1 = statistics_from_values([URBAN, URBAN], unique=True)
        view = TerritorialOverview(); self.addCleanup(view.close)
        view.set_statistics({'source_statistics': data, 'r1_statistics': r1})
        self.assertIn('Base catastral: 2 predios activos; 1 predios cancelados', view.note.text())
        self.assertIn('R1: 1 predios', view.note.text())
        self.assertIn('otros/sin estado: 1', view.note.text())

    def test_missing_state_is_unavailable_not_all_active(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'predios.csv'; path.write_text(URBAN + '\n')
            data = read_source_statistics({}, '', 'CICA', SimpleNamespace(columns=('numero_predial',), csv_path=path))
        self.assertIsNone(data['status_counts']['active'])
        self.assertIsNone(data['status_counts']['cancelled'])
        self.assertEqual(data['total'], 1)

    def test_database_state_aggregates_count_null_and_other_states(self):
        from qgis_control_calidad.territorial_statistics import read_status_counts
        class Cursor:
            def execute(self, statement): self.query = render(statement)
            def fetchall(self): return [(7, 2, 1)]
        cursor = Cursor()
        counts = read_status_counts(cursor, 'datos', 'cica_predio', {'numero_predial', 'estado'}, 'CICA')
        self.assertEqual((counts['active'], counts['cancelled'], counts['other']), (7, 2, 1))
        self.assertIn("= 'ACTIVO'", cursor.query)
        self.assertIn("= 'CANCELADO'", cursor.query)
        self.assertIn('IS NULL', cursor.query)

    def test_internal_cancellation_does_not_multiply_predios_with_multiple_novelties(self):
        import sqlite3
        from qgis_control_calidad.territorial_statistics import read_status_counts
        db = sqlite3.connect(':memory:'); self.addCleanup(db.close)
        db.execute("ATTACH DATABASE ':memory:' AS datos")
        metadata = {
            'ilc_datosadicionaleslevantamientocatastral': ['t_id', 'ilc_predio'],
            'ilc_estructuranovedadnumeropredial': ['ilc_dtsdcnltmntctstral_novedad_numeros_prediales', 'tipo_novedad'],
            'ilc_estructuranovedadnumeropredial_tipo_novedad': ['t_id', 'ilicode'],
        }
        db.execute('CREATE TABLE datos.ilc_predio (t_id INTEGER)')
        db.executemany('INSERT INTO datos.ilc_predio VALUES (?)', [(1,), (2,), (3,)])
        for table, columns in metadata.items():
            db.execute('CREATE TABLE datos.' + table + ' (' + ', '.join(columns) + ')')
        db.executemany('INSERT INTO datos.ilc_datosadicionaleslevantamientocatastral VALUES (?, ?)', [(10, 1), (20, 2)])
        db.executemany('INSERT INTO datos.ilc_estructuranovedadnumeropredial VALUES (?, ?)', [(10, 100), (10, 101), (20, 102)])
        db.executemany('INSERT INTO datos.ilc_estructuranovedadnumeropredial_tipo_novedad VALUES (?, ?)', [(100, 'Cancelacion'), (101, 'Cancelacion_por_Englobe'), (102, 'Otra_Novedad')])
        class Cursor:
            def execute(self, statement, params=()):
                query = render(statement)
                if 'information_schema.columns' in query:
                    self.rows = [(table, column) for table, columns in metadata.items() for column in columns]
                else:
                    self.rows = db.execute(query).fetchall()
            def fetchall(self): return self.rows
        counts = read_status_counts(Cursor(), 'datos', 'ilc_predio', {'numero_predial_nacional', 't_id'}, 'Modelo Interno de Levantamiento 1.0')
        self.assertEqual((counts['active'], counts['cancelled'], counts['other']), (2, 1, 0))
