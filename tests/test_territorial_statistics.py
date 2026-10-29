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
        dialog = TerritorialFilterDialog('all', (), self.data)
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
        dialog = TerritorialFilterDialog('all', (), self.data)
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
            self.assertEqual(data['r1_statistics']['total'], 3)
            dialog = TerritorialFilterDialog('urban+rural', (), lambda: data)
            self.addCleanup(dialog.close); dialog.load_codes()
            self.assertIn('Fuente de validación: 2 de 2', dialog.selection_statistics.text())
            self.assertIn('R1: 2 de 3', dialog.selection_statistics.text())
            dialog.search.setText(URBAN); dialog.select_all_button.click()
            self.assertIn('Fuente de validación: 1 de 2', dialog.selection_statistics.text())
            self.assertIn('R1: 2 de 3', dialog.selection_statistics.text())
            row = next(item for item in dialog.items() if item.data(0, Qt.UserRole) == URBAN)
            self.assertEqual((row.text(2), row.text(3)), ('1', '2'))
            # R1-only codes remain visible under the appropriate scope, source count zero.
            dialog.scope.set_scope('all'); dialog.search.clear()
            row = next(item for item in dialog.items() if item.data(0, Qt.UserRole) == CENTER)
            self.assertEqual((row.text(2), row.text(3)), ('0', '1'))

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
