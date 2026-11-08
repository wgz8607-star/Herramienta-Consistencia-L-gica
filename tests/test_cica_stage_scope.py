import sqlite3
import unittest
from unittest.mock import patch
from qgis_control_calidad.cica_stage_scope import apply_stage_scope
from qgis_control_calidad.dialog import RuleWorker
from qgis_control_calidad.ingestion import CicaIngestionDialog
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtCore import Qt
from test_temporary_references import app

FILTER="cp.etapa IN ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO')"
QUERY='SELECT count(*) FROM cica_predio cp WHERE '+FILTER+" AND cp.estado='ACTIVO'"


class StageScopeTests(unittest.TestCase):
    def test_default_keeps_statement_and_custom_or_all_only_changes_stage_scope(self):
        self.assertEqual(apply_stage_scope(QUERY,{}),QUERY)
        db=sqlite3.connect(':memory:')
        try:
            db.execute('CREATE TABLE cica_predio (etapa TEXT,estado TEXT)')
            db.executemany('INSERT INTO cica_predio VALUES (?,?)',[('CONTROL_CALIDAD_GENERAL','ACTIVO'),('CONTROL_CALIDAD_GRUPO','ACTIVO'),('ASIGNADO','ACTIVO'),(None,'ACTIVO'),('ASIGNADO','CANCELADO')])
            for mode,stages,count in [('default',(),2),('custom',('ASIGNADO',),1),('custom',('',),1),('all',(),4)]:
                query=apply_stage_scope(QUERY,{'stage_mode':mode,'stages':stages})
                self.assertIn("cp.estado='ACTIVO'",query)
                self.assertEqual(db.execute(query.replace('::text','').replace("E'","'")).fetchone()[0],count)
        finally:db.close()

    def test_literals_comments_and_other_business_stage_conditions_are_not_rewritten(self):
        statement="SELECT '"+FILTER.replace("'","''")+"' AS texto FROM cica_predio cp WHERE "+FILTER+" AND cp.etapa <> 'SIN_ASIGNAR' -- "+FILTER
        result=apply_stage_scope(statement,{'stage_mode':'all'})
        self.assertIn("cp.etapa <> 'SIN_ASIGNAR'",result)
        self.assertTrue(result.endswith('-- '+FILTER))
        self.assertIn("'CONTROL_CALIDAD_GENERAL''",result)
        self.assertEqual(result.count('(TRUE)'),1)
        with self.assertRaises(ValueError):apply_stage_scope(QUERY,{'stage_mode':'custom','stages':()})
        escaped=apply_stage_scope(QUERY,{'stage_mode':'custom','stages':("X'); DROP TABLE x; --",)})
        self.assertIn("E'X''); DROP TABLE x; --'",escaped)

    def test_worker_uses_runtime_scope_and_keeps_input_statement(self):
        worker=RuleWorker({},'base','','',[],cica_selection={'stage_mode':'custom','stages':('ASIGNADO',)})
        result=worker.resolve_sql('SELECT * FROM {esquema}.cica_predio cp WHERE '+FILTER)
        self.assertIn("E'ASIGNADO'",result)
        self.assertIn('base.cica_predio',result)

    def test_stage_scope_is_visible_on_main_screen_and_custom_selection_is_shown(self):
        from qgis_control_calidad.dialog import ControlCalidadDialog, SNC_ENVIRONMENT
        dialog=ControlCalidadDialog();self.addCleanup(dialog.close)
        dialog.model.setCurrentText('CICA')
        dialog.update_cica_stage_presentation()
        self.assertFalse(dialog.cica_stage_status.isHidden())
        self.assertFalse(dialog.cica_stage_button.isHidden())
        self.assertIn('Validación de predios en etapas de control de calidad',dialog.cica_stage_status.text())
        dialog.cica_selection={'stage_mode':'custom','stages':('ASIGNADO','VALIDADO'),'source_kind':'files'}
        dialog.update_cica_stage_presentation()
        self.assertIn('Validación personalizada de etapas',dialog.cica_stage_status.text())
        self.assertIn('ASIGNADO',dialog.cica_stage_status.text())
        dialog.environment.blockSignals(True);dialog.environment.setCurrentText(SNC_ENVIRONMENT);dialog.environment.blockSignals(False)
        dialog.update_cica_stage_presentation()
        self.assertTrue(dialog.cica_stage_button.isHidden())

    def test_reopening_file_source_preserves_custom_stage_selection(self):
        import csv,tempfile
        from pathlib import Path
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'predio.csv'
            with path.open('w',newline='') as stream:
                csv.writer(stream).writerows([['0842101000001','ASIGNADO'],['0842101000002','VALIDADO']])
            snapshot=SimpleNamespace(columns=('numero_predial','etapa'),csv_path=path,filename='predio.csv',row_count=2)
            selection={'stage_mode':'custom','stages':('ASIGNADO',),'source_kind':'files','municipality':''}
            dialog=CicaIngestionDialog(references={'cica_predio':snapshot},initial_selection=selection)
            try:
                self.assertEqual(dialog.stage_mode.currentData(),'custom')
                self.assertEqual(dialog.selected_source_filter()['stages'],('ASIGNADO',))
                self.assertTrue(dialog.custom_stage_selection_confirmed)
                self.assertFalse(dialog.stage_selector_button.isHidden())
            finally:dialog.close()

    def test_default_stage_selector_is_hidden_and_custom_selection_uses_separate_window(self):
        dialog=CicaIngestionDialog();self.addCleanup(dialog.close)
        with patch.object(dialog,'refresh_repository_date'):dialog.source_mode.setCurrentIndex(1)
        dialog.repository_options=[('08421','ASIGNADO',3),('08421','TRAMITADO',2)]
        dialog.municipality.addItem('08421','08421');dialog.municipality.setCurrentIndex(1)
        self.assertEqual(dialog.selected_source_filter()['stage_mode'],'default')
        self.assertEqual(dialog.selected_source_filter()['stages'],())
        self.assertTrue(dialog.stages.isHidden())
        dialog.stage_mode.setCurrentIndex(1)
        self.assertTrue(dialog.stages.isHidden())
        with patch('qgis_control_calidad.ingestion.QDialog.exec_',return_value=QDialog.Accepted):dialog.open_stage_selector()
        self.assertTrue(dialog.custom_stage_selection_confirmed)
        self.assertEqual(dialog.selected_source_filter()['stages'],('ASIGNADO','TRAMITADO'))
        self.assertTrue(dialog.stages.isHidden())
        self.assertEqual(dialog.stage_mode.count(),2)
