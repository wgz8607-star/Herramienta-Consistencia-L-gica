import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from qgis.PyQt.QtWidgets import QMessageBox
from administrador_reglas_qgis.repositorio import COLUMNS, RuleUpload, create_template, read_rules, fetch_existing, make_plan, insert_import
from administrador_reglas_qgis.dialog import AdministratorDialog
from administrador_reglas_qgis import servicio
from test_rule_upload import render, values


class SqliteCursor:
    """Execute the standard SELECT/INSERT/UPDATE SQL against a real transaction."""
    def __init__(self, owner):
        self.owner = owner; self.cursor = owner.db.cursor()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.cursor.close()
    def execute(self, statement, params=()):
        query = render(statement); self.owner.events.append(query)
        if not query.startswith(('SET LOCAL', 'LOCK TABLE')):
            self.cursor.execute(query.replace('%s', '?'), params)
    def executemany(self, statement, records):
        query = render(statement); self.owner.events.append(query)
        self.cursor.executemany(query.replace('%s', '?'), records)
    @property
    def rowcount(self):
        return self.cursor.rowcount
    def fetchall(self):
        return self.cursor.fetchall()


class SqliteRepository:
    def __init__(self, records):
        self.db = sqlite3.connect(':memory:'); self.events = []
        self.db.execute("ATTACH DATABASE ':memory:' AS revision")
        definitions = ', '.join('"' + c + '" ' + ('INTEGER' if c in ('activa', 'orden', 'version_publicada') else 'TEXT') for c in COLUMNS)
        self.db.execute('CREATE TABLE revision.mis_reglas (id INTEGER PRIMARY KEY AUTOINCREMENT, ' + definitions + ", CHECK(codigo_regla <> 'bad'))")
        self.db.executemany('INSERT INTO revision.mis_reglas (' + ','.join(COLUMNS) + ') VALUES (' + ','.join('?' for _ in COLUMNS) + ')', records)
        self.db.commit()
    def cursor(self):
        return SqliteCursor(self)
    def __enter__(self):
        return self
    def __exit__(self, kind, value, traceback):
        self.db.commit() if kind is None else self.db.rollback()
    def close(self):
        self.db.close()


class ReplacementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)

    def database(self, records):
        connection = SqliteRepository(records); self.addCleanup(connection.close)
        return connection

    def plan(self, connection, records):
        existing = fetch_existing(connection, 'mis_reglas', 'revision', True)
        return make_plan('mis_reglas', [RuleUpload(index, record) for index, record in enumerate(records, 2)], existing,
                         schema='revision', catalog_target=True, replace_by_order=True)

    def test_same_order_replaces_row_and_preserves_technical_id(self):
        original = values('001')
        connection = self.database([original])
        replacement = list(values('002')); replacement[4] = 'SELECT nueva_sentencia'; replacement = tuple(replacement)
        plan = self.plan(connection, [replacement])
        self.assertEqual(len(plan.inserts), 0); self.assertEqual(len(plan.updates), 1)
        self.assertEqual(plan.states, ['Reemplaza por orden'])
        with connection:
            result = insert_import(connection, plan)
        self.assertEqual(result, {'inserted': 0, 'updated': 1, 'unchanged': 0})
        row = connection.db.execute('SELECT id, codigo_regla, sentencia_sql FROM revision.mis_reglas').fetchone()
        self.assertEqual(row, (1, '002', 'SELECT nueva_sentencia'))
        self.assertTrue(any(q.startswith('UPDATE') for q in connection.events))
        self.assertFalse(any(q.startswith('DELETE') for q in connection.events))

    def test_mixed_insert_replace_and_unchanged_have_correct_counts(self):
        original = values('001')
        same = list(values('003')); same[7] = 300
        connection = self.database([original, tuple(same)])
        replacement = list(original); replacement[5] = 'Nueva descripción'
        new = list(values('002')); new[7] = 200
        plan = self.plan(connection, [tuple(replacement), tuple(new), tuple(same)])
        with connection:
            result = insert_import(connection, plan)
        self.assertEqual(result, {'inserted': 1, 'updated': 1, 'unchanged': 1})
        self.assertEqual(connection.db.execute('SELECT count(*) FROM revision.mis_reglas').fetchone()[0], 3)

    def test_same_order_does_not_mix_components_or_versions(self):
        first = list(values('001')); first[1] = 'Administrativas'
        second = list(values('002')); second[1] = 'Fisicas'
        third = list(values('003', version='V2_SNC')); third[1] = 'Administrativas'
        connection = self.database([tuple(first), tuple(second), tuple(third)])
        modified = list(first); modified[4] = 'SELECT modificada'
        with connection:
            insert_import(connection, self.plan(connection, [tuple(modified)]))
        rows = connection.db.execute('SELECT codigo_regla, sentencia_sql FROM revision.mis_reglas ORDER BY id').fetchall()
        self.assertEqual(rows, [('001', 'SELECT modificada'), ('002', second[4]), ('003', third[4])])

    def test_failure_after_update_rolls_back_replacement_and_all_inserts(self):
        original = values('001'); connection = self.database([original])
        replacement = list(original); replacement[4] = 'SELECT cambio'
        new = list(values('bad')); new[7] = 200
        plan = self.plan(connection, [tuple(replacement), tuple(new)])
        with self.assertRaises(sqlite3.IntegrityError):
            with connection:
                insert_import(connection, plan)
        self.assertEqual(connection.db.execute('SELECT codigo_regla, sentencia_sql FROM revision.mis_reglas').fetchall(), [('001', original[4])])

    def test_ambiguous_repeated_order_in_database_is_rejected(self):
        connection = self.database([values('001'), values('002')])
        with self.assertRaisesRegex(ValueError, 'varias reglas'):
            self.plan(connection, [values('003')])

    def test_repeated_order_in_excel_is_rejected_in_replacement_mode(self):
        path = Path(self.temp.name) / 'reglas.xlsx'
        create_template(path, [values('001'), values('002')])
        with self.assertRaisesRegex(ValueError, 'orden duplicado'):
            read_rules(path, replace_by_order=True)
        self.assertEqual(len(read_rules(path)), 2)

    def test_code_in_another_order_is_not_overwritten_accidentally(self):
        first = values('001'); second = list(values('002')); second[7] = 200
        connection = self.database([first, tuple(second)])
        conflicting = list(first); conflicting[2] = '002'
        with self.assertRaisesRegex(ValueError, 'otro orden'):
            self.plan(connection, [tuple(conflicting)])

    def test_unchanged_row_requires_no_update(self):
        connection = self.database([values()])
        plan = self.plan(connection, [values()])
        self.assertEqual(plan.changes, 0)
        with connection:
            result = insert_import(connection, plan)
        self.assertEqual(result, {'inserted': 0, 'updated': 0, 'unchanged': 1})
        self.assertFalse(any(q.startswith('UPDATE') or q.startswith('INSERT') for q in connection.events))

    def test_non_header_metadata_is_not_changed_on_an_unchanged_row(self):
        first = list(values('001')); first[9] = True
        second = list(values('002')); second[7] = 200; second[8] = ''; second[9] = False
        connection = self.database([tuple(first), tuple(second)])
        plan = self.plan(connection, [tuple(second)])
        self.assertEqual(plan.changes, 0)

    def test_publication_changes_are_included_in_replacement_validation(self):
        old = list(values('001', active=True, published=True))
        changed = list(old); changed[9] = False
        new = list(values('002', version='V2_SNC', active=True, published=True)); new[7] = 200
        plan = make_plan('reglas_cargue_snc_cica', [RuleUpload(2, tuple(changed)), RuleUpload(3, tuple(new))], [tuple(old)], replace_by_order=True)
        self.assertEqual(len(plan.updates), 1); self.assertEqual(plan.updates[0][1][9], False)
        with self.assertRaisesRegex(ValueError, 'una sola versión'):
            make_plan('reglas_cargue_snc_cica', [RuleUpload(2, tuple(new))], [tuple(old)], replace_by_order=True)

    def test_unexpected_update_count_aborts_instead_of_reporting_success(self):
        original = values('001'); connection = self.database([original])
        modified = list(original); modified[4] = 'SELECT cambio'
        plan = self.plan(connection, [tuple(modified)])
        execute = SqliteCursor.executemany
        def denied(cursor, statement, records):
            query = render(statement)
            return execute(cursor, query + ' AND 0=1' if query.startswith('UPDATE') else statement, records)
        with patch.object(SqliteCursor, 'executemany', denied):
            with self.assertRaisesRegex(ValueError, 'No se reemplazaron'):
                with connection:
                    insert_import(connection, plan)
        self.assertEqual(connection.db.execute('SELECT sentencia_sql FROM revision.mis_reglas').fetchone()[0], original[4])

    def test_confirmation_shows_insert_and_replace_details_before_writing(self):
        connection = self.database([values('001')])
        replacement = list(values('002')); replacement[4] = 'SELECT consulta_nueva'
        new = list(values('003')); new[7] = 200
        plan = self.plan(connection, [tuple(replacement), tuple(new)])
        dialog = AdministratorDialog(); self.addCleanup(dialog.close)
        dialog.mode.setCurrentIndex(1); dialog.host.setText('servidor'); dialog.user.setText('administrador')
        dialog.schema.blockSignals(True); dialog.schema.addItem('revision'); dialog.schema.blockSignals(False)
        dialog.table.addItem('mis_reglas', {'name': 'mis_reglas', 'insert': True})
        dialog.show_plan(plan)
        self.assertTrue(dialog.load_button.isEnabled())
        self.assertIn('Anterior:', dialog.fields_text.toPlainText())
        captured = []
        def cancel(message):
            captured.append(message.text() + message.detailedText())
            return QMessageBox.Cancel
        with patch.object(QMessageBox, 'exec_', cancel), patch.object(servicio, 'apply_plan') as apply:
            dialog.apply()
        apply.assert_not_called()
        self.assertIn('Filas nuevas: 1', captured[0]); self.assertIn('Filas que se reemplazarán: 1', captured[0])
        self.assertIn('001', captured[0]); self.assertIn('002', captured[0])
        self.assertIn('SELECT consulta_nueva', captured[0])
