from collections import Counter
import sqlite3
import unittest
from unittest.mock import patch
from qgis_control_calidad.general_report_counts import apply_unique_filtered_r1_count
from qgis_control_calidad.dialog import RuleWorker
from test_cica_source_selection import render
from qgis_control_calidad.territorial_scope import predicate


class Cursor:
    def __init__(self,connection):self.connection=connection
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def execute(self,query):
        self.connection.queries.append(query)
        self.cursor=self.connection.db.execute(query.replace('::text','').replace('pg_temp.','temp.'))
    def fetchone(self):return self.cursor.fetchone()


class Connection:
    def __init__(self,filter_sql):
        self.queries=[];self.db=sqlite3.connect(':memory:')
        self.db.create_function('btrim',1,lambda value:value.strip() if value is not None else None)
        self.db.execute('CREATE TEMP TABLE reference_r1 (numero_predial TEXT)')
        self.db.executemany('INSERT INTO reference_r1 VALUES (?)',[(value,) for value in (
            '084210100000100001000000000001','084210100000100001000000000001',
            ' 084210100000100001000000000001 ', '084210100000100001000000000002',
            '084210000000100001000000000003','130060100000100001000000000004',None,'','   ')])
        if filter_sql:
            self.db.execute('CREATE TEMP VIEW selected_r1 AS SELECT * FROM reference_r1 WHERE '+filter_sql.replace('::text',''))
    def cursor(self):return Cursor(self)


class GeneralReportR1CountTests(unittest.TestCase):
    def test_count_uses_filtered_source_and_preserves_reference_duplicates(self):
        prefix='08421010000010000'
        for filtered,expected in ((False,4),(True,2)):
            db=Connection(render(predicate('numero_predial','urban',(prefix,))) if filtered else '')
            try:
                before=Counter(db.db.execute('SELECT * FROM reference_r1').fetchall())
                worker=RuleWorker({},'base','','',[],references={'R1':object()})
                if filtered:worker.scope_views={('pg_temp','reference_r1'):'selected_r1'}
                rows=[{'id':77,'descripcion':'Todos los registros de R1','cantidad':999,'reglas_validacion_afectadas':'8.23'},
                      {'id':1,'descripcion':'Otros registros','cantidad':9}]
                apply_unique_filtered_r1_count(db,rows,worker.resolve_sql)
                self.assertEqual(rows[0]['cantidad'],expected)
                self.assertEqual(rows[1]['cantidad'],9)
                self.assertEqual(rows[0]['id'],77)
                self.assertEqual(rows[0]['reglas_validacion_afectadas'],'8.23')
                self.assertEqual(before,Counter(db.db.execute('SELECT * FROM reference_r1').fetchall()))
                self.assertEqual(len(db.queries),1)
                self.assertIn('selected_r1' if filtered else 'reference_r1',db.queries[0])
            finally:db.db.close()

    def test_empty_filtered_r1_is_zero_and_column_case_is_preserved(self):
        db=Connection('FALSE')
        try:
            worker=RuleWorker({},'base','','',[],references={'R1':object()})
            worker.scope_views={('pg_temp','reference_r1'):'selected_r1'}
            rows=[{'Descripcion':'Todos los registros del R1','Cantidad':99}]
            apply_unique_filtered_r1_count(db,rows,worker.resolve_sql)
            self.assertEqual(rows,[{'Descripcion':'Todos los registros del R1','Cantidad':0}])
        finally:db.db.close()

    def test_worker_emits_the_corrected_total_without_changing_report_statement(self):
        from types import SimpleNamespace
        from test_temporary_references import FakeConnection, FakeCursor
        class ReportCursor(FakeCursor):
            def execute(self,query):
                super().execute(query)
                if query == 'REPORT_R1':
                    self.description=[SimpleNamespace(name=name) for name in ('id','descripcion','cantidad')]
            def fetchall(self):
                return [(77,'Todos los registros de R1',8)]
            def fetchone(self):return (2,)
        class ReportConnection(FakeConnection):
            def cursor(self):return ReportCursor(self)
        connection=ReportConnection()
        worker=RuleWorker({},'base','','',[],general_report_path='REPORT_R1',references={'R1':object()},model='Interno')
        reports=[];errors=[]
        worker.general_report.connect(lambda rows,error:reports.append((rows,error)))
        worker.fatal_error.connect(errors.append)
        with patch('qgis_control_calidad.dialog.psycopg2.connect',return_value=connection),patch('qgis_control_calidad.dialog.install_reference',side_effect=lambda conn,ref:conn.tables.add('reference_r1')),patch('qgis_control_calidad.dialog.optimize_temporary_tables'):
            worker.run()
        self.assertEqual(errors,[])
        self.assertEqual(reports,[([{'id':77,'descripcion':'Todos los registros de R1','cantidad':2}], '')],connection.events)
        self.assertEqual(worker.general_report_path,'REPORT_R1')
        self.assertTrue(connection.closed)

    def test_other_report_items_do_not_trigger_an_extra_query(self):
        rows=[{'descripcion':'Otros predios','cantidad':100}]
        from unittest.mock import Mock
        connection=Mock();resolve=Mock()
        self.assertIs(apply_unique_filtered_r1_count(connection,rows,resolve),rows)
        connection.cursor.assert_not_called();resolve.assert_not_called()
