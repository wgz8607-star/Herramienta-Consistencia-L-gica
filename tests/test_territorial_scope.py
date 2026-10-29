import sqlite3
import unittest
from unittest.mock import patch
from psycopg2 import sql
from qgis_control_calidad.territorial_scope import predicate, resolve_scope, install_scope
from test_temporary_references import render, ControlCalidadDialog


class ScopeTests(unittest.TestCase):
    def test_npn_positions_and_numeric_center_filter(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.create_function('btrim', 1, lambda v: v.strip() if v else v)
        db.create_function('regexp', 2, lambda pattern, value: bool(__import__('re').search(pattern, value or '')))
        db.execute('CREATE TABLE cases (numero_predial TEXT)')
        numbers = ['08421' + code + '0' * 23 for code in ('00', '01', '02', '09', '99', 'AA')] + ['', None]
        db.executemany('INSERT INTO cases VALUES (?)', [(n,) for n in numbers])
        for scope, expected in [('urban', [numbers[1]]), ('rural', [numbers[0]]), ('center', numbers[2:5])]:
            query = render(predicate('numero_predial', scope)).replace('::text', '').replace(' ~ ', ' REGEXP ')
            self.assertEqual([row[0] for row in db.execute('SELECT numero_predial FROM cases WHERE ' + query)], expected)

    def test_same_scope_targets_cica_and_both_references_without_literals(self):
        mapping = {('city', 'cica_predio'): 'validation_scope_0', ('pg_temp', 'reference_r1'): 'validation_scope_1', ('pg_temp', 'reference_r2'): 'validation_scope_2'}
        query = "SELECT 'city.cica_predio' FROM city.cica_predio p JOIN pg_temp.reference_r1 r ON true JOIN pg_temp.reference_r2 s ON true -- city.cica_predio"
        out = resolve_scope(query, mapping)
        self.assertIn("'city.cica_predio'", out)
        self.assertIn('-- city.cica_predio', out)
        for view in mapping.values():
            self.assertIn('pg_temp.' + view, out)

    def test_unaliased_table_keeps_original_column_qualifier(self):
        mapping = {('city', 'cica_predio'): 'validation_scope_0'}
        out = resolve_scope('SELECT cica_predio.numero_predial FROM city.cica_predio WHERE true', mapping)
        self.assertIn('pg_temp.validation_scope_0 AS "cica_predio" WHERE', out)
        out = resolve_scope('SELECT p.numero_predial FROM city.cica_predio p', mapping)
        self.assertTrue(out.endswith('pg_temp.validation_scope_0 p'))

    def test_all_avoids_database_and_invalid_selection_fails(self):
        self.assertEqual(install_scope(None, 'city', set(), [], 'all'), {})
        with self.assertRaises(ValueError):
            install_scope(None, 'city', set(), [], None)

    def test_scope_views_filter_cica_and_both_reference_sources_without_writes(self):
        class Database:
            def __init__(self):
                self.statements = []; self.rows = []
            def cursor(self): return self
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def execute(self, statement, params=()):
                query = render(statement); self.statements.append(query)
                if 'information_schema.columns' in query:
                    self.rows = [('cica_predio',), ('cica_seguimiento_control',)]
                elif 'pg_attribute' in query:
                    self.rows = [('numero_predial',)]
                else:
                    self.rows = []
            def fetchall(self): return self.rows
        db = Database()
        with patch.object(sql.Identifier, 'as_string', lambda self, conn: render(self)):
            mapping = install_scope(db, 'city', {'cica_predio'}, ['reference_r1', 'reference_r2'], 'rural')
        self.assertIn(('pg_temp', 'cica_predio'), mapping)
        self.assertNotIn(('city', 'cica_predio'), mapping)
        self.assertEqual(len(mapping), 4)
        views = [q for q in db.statements if q.startswith('CREATE TEMP VIEW')]
        self.assertEqual(len(views), 4)
        self.assertTrue(all("6, 2) = '00'" in q for q in views))
        self.assertFalse(any(q.startswith(('UPDATE', 'DELETE', 'INSERT', 'DROP')) for q in db.statements))

    def test_advanced_filter_defaults_to_all_for_both_models(self):
        widget = ControlCalidadDialog()
        self.addCleanup(widget.close)
        for model in ('CICA', 'Modelo Interno de Levantamiento 1.0'):
            widget.model.setCurrentText(model)
            self.assertEqual(widget.scope_selection, 'all')
            self.assertEqual(widget.scope_prefixes, ())
            self.assertEqual(widget.left_tabs.tabText(widget.advanced_filter_tab_index), 'Estadística y filtro avanzado')
            self.assertFalse(widget.left_tabs.isTabEnabled(widget.advanced_filter_tab_index))

    def test_17_digit_prefixes_are_validated_and_combined_with_scope(self):
        from qgis_control_calidad.territorial_scope import normalize_prefixes
        self.assertEqual(normalize_prefixes(['08421010000010000', '08421010000010000']), ('08421010000010000',))
        for invalid in ('08421', '0842101000001', '084210100000100000', "084210100000'"):
            with self.assertRaises(ValueError):
                normalize_prefixes([invalid])

    def test_read_prefixes_from_local_snapshot_preserves_zeroes(self):
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from qgis_control_calidad.territorial_filter import read_prefixes
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.csv'
            path.write_text('"0842101000001000000000000000000"\n"0842100000001000000000000000000"\n"invalid"\n')
            snapshot = SimpleNamespace(columns=('numero_predial',), csv_path=path)
            with patch('qgis_control_calidad.territorial_filter.psycopg2.connect') as connect:
                self.assertEqual(read_prefixes({}, '', 'CICA', snapshot), ['08421000000010000', '08421010000010000'])
            connect.assert_not_called()

    def test_editor_defaults_to_all_and_retains_selection_across_search(self):
        from qgis_control_calidad.territorial_filter import TerritorialFilterDialog
        dialog = TerritorialFilterDialog('all', ('08421010000010000',), lambda: [])
        self.addCleanup(dialog.close)
        self.assertEqual(dialog.scope.currentData(), 'all')
        dialog.search.setText('not-found')
        self.assertEqual(dialog.selected_prefixes(), ('08421010000010000',))
        dialog.clear_codes()
        self.assertEqual(dialog.selected_prefixes(), ())
