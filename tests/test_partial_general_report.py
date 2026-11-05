from pathlib import Path
from types import SimpleNamespace
import sqlite3
import unittest
from unittest.mock import patch
from qgis_control_calidad.partial_general_report import alphanumeric_report_sql,mark_unevaluated_items,NOT_EVALUATED
from qgis_control_calidad.gdb_dependencies import requires_gdb
from qgis_control_calidad.dialog import RuleWorker
from test_temporary_references import FakeConnection,FakeCursor

STATEMENT="""WITH tb1 AS (
SELECT 1 id, COUNT(*) cantidad FROM {esquema}.cica_predio
UNION ALL
(WITH capas AS (
 SELECT codigo FROM {esquema}.u_terreno_ctm12
 UNION ALL SELECT codigo FROM {esquema}.r_terreno_ctm12
) SELECT 2 id, COUNT(*) cantidad FROM capas)
UNION ALL
SELECT 3 id, COUNT(*) cantidad FROM {esquema}.cica_predio WHERE estado='ACTIVO'
), tb2(id,descripcion) AS (VALUES (1,'Alfa'),(2,'Geo'),(3,'Activos'))
SELECT tb2.id,tb2.descripcion,tb1.cantidad FROM tb1 JOIN tb2 ON tb1.id=tb2.id ORDER BY tb2.id"""


class PartialGeneralReportTests(unittest.TestCase):
    def test_nested_unions_are_omitted_by_whole_indicator_and_other_counts_execute(self):
        statement,omitted=alphanumeric_report_sql(STATEMENT)
        self.assertEqual(omitted,(2,))
        self.assertFalse(requires_gdb(statement))
        self.assertIn("WHERE estado='ACTIVO'",statement)
        self.assertIn("(2,'Geo')",statement)
        db=sqlite3.connect(':memory:')
        try:
            db.execute('CREATE TABLE cica_predio (estado TEXT)')
            db.executemany('INSERT INTO cica_predio VALUES (?)',[('ACTIVO',),('ACTIVO',),('CANCELADO',)])
            cursor=db.execute(statement.replace('{esquema}.','').replace('::bigint',''))
            rows=[dict(zip([c[0] for c in cursor.description],row)) for row in cursor.fetchall()]
            mark_unevaluated_items(rows,omitted)
            self.assertEqual([row['cantidad'] for row in rows],[3,NOT_EVALUATED,2])
        finally:db.close()

    def test_actual_cica_template_identifies_four_geographic_indicators(self):
        path=Path(__file__).parents[1]/'qgis_control_calidad/resources/sql/rules_cica_db/Reportes/reportes.sql'
        original=path.read_text();statement,ids=alphanumeric_report_sql(original)
        self.assertEqual(ids,(47,48,49,54))
        self.assertFalse(requires_gdb(statement))
        self.assertEqual(path.read_text(),original)
        self.assertIn('SELECT 47 AS id, NULL::bigint AS cantidad',statement)

    def test_unsupported_report_is_rejected_instead_of_fabricating_counts(self):
        with self.assertRaises(ValueError):
            alphanumeric_report_sql('SELECT COUNT(*) FROM {esquema}.u_terreno_ctm12')

    def test_worker_emits_numeric_alpha_counts_and_explicit_unevaluated_geo(self):
        class ReportCursor(FakeCursor):
            def execute(self,query):
                super().execute(query)
                if query.startswith('WITH tb1'):
                    self.description=[SimpleNamespace(name=name) for name in ('id','descripcion','cantidad')]
            def fetchall(self):return [(1,'Alfa',3),(2,'Geo',None),(3,'Activos',2)]
        class Connection(FakeConnection):
            def cursor(self):return ReportCursor(self)
        connection=Connection();worker=RuleWorker({},'base','','',[],general_report_path=STATEMENT)
        reports=[];worker.general_report.connect(lambda rows,error:reports.append((rows,error)))
        with patch('qgis_control_calidad.dialog.psycopg2.connect',return_value=connection):worker.run()
        self.assertEqual(reports[0][1],'')
        self.assertEqual([row['cantidad'] for row in reports[0][0]],[3,NOT_EVALUATED,2])
        self.assertEqual(worker.general_report_path,STATEMENT)
        self.assertTrue(connection.closed)
