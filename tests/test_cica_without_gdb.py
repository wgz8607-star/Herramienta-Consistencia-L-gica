from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import unittest
from openpyxl import Workbook
from qgis_control_calidad.gdb_dependencies import requires_gdb, partition_rules
from qgis_control_calidad import dialog as module
from qgis_control_calidad.report_exceptions import prepare_validation_index
from test_temporary_references import app


class GdbDependencyTests(unittest.TestCase):
    def test_detection_ignores_literals_comments_and_numeric_area_fields(self):
        for statement in [
            "SELECT area_geografica FROM {esquema}{punto}cica_predio",
            "SELECT 'u_terreno.geom' FROM {esquema}.cica_predio -- JOIN u_terreno",
            "SELECT 1 /* ST_Area(x.geom) FROM {esquema}.u_terreno */",
            "SELECT * FROM {esquema_r1}.{tabla_r1}",
        ]:
            self.assertFalse(requires_gdb(statement), statement)
        for statement in [
            'SELECT * FROM {esquema}{punto}u_terreno_ctm12',
            'SELECT * FROM {esquema}."r_unidad_ctm12"',
            'SELECT * FROM pg_temp.u_terreno_ctm12',
            'SELECT ST_Area(cp.geom) FROM {esquema}.cica_predio cp',
            'SELECT * FROM {esquema}{punto}poligonos',
        ]:
            self.assertTrue(requires_gdb(statement), statement)

    def test_published_cica_rules_are_partitioned_without_modification(self):
        root=Path(module.__file__).parent/'resources/sql/rules_cica_db'
        rules=[(p.parent.name,p.stem,p.read_text(),'') for p in root.rglob('*.sql') if p.parent.name!='Reportes']
        original=list(rules)
        executable,omitted=partition_rules(rules,False)
        omitted_names={r[1] for r in omitted}
        self.assertTrue({'regla_1_24','struct_01','struct_02','regla_3_6','regla_3_8','regla_3_33'} <= omitted_names)
        self.assertTrue({'regla_1_51','regla_1_53','regla_1_55'} <= {r[1] for r in executable})
        self.assertEqual(len(executable)+len(omitted),len(rules))
        self.assertEqual(rules,original)
        self.assertEqual(partition_rules(rules,True),(original,[]))


class WithoutGdbUiTests(unittest.TestCase):
    def setUp(self):
        self.widget=module.ControlCalidadDialog()
        self.widget.model.blockSignals(True);self.widget.model.setCurrentText('CICA');self.widget.model.blockSignals(False)
        self.widget.environment.blockSignals(True);self.widget.environment.setCurrentText('Validaciones del modelo');self.widget.environment.blockSignals(False)
        self.widget.cica_references={'cica_predio':SimpleNamespace(filename='predio.csv',fingerprint='predio',close=lambda:None)}
        self.alpha=('Administrativas','regla_alpha','SELECT * FROM {esquema}.cica_predio','')
        self.geo=('Fisicas','regla_geo','SELECT ST_Area(t.geom) FROM {esquema}.u_terreno_ctm12 t JOIN {esquema_r2}.{tabla_r2} r ON true','')
        self.report='SELECT * FROM {esquema}.r_unidad_ctm12'
        self.widget.repository_rules=[dict(component=r[0],rule=r[1],sql=r[2],description=r[3],type='CONTROL') for r in [self.alpha,self.geo]]+[dict(component='Reportes',rule='reportes',type='REPORTE',sql=self.report)]
        self.widget.selected_sql_version={'codigo':'V2_29_07_2024'}
        self.widget.refresh_categories()
        self.params={'dbname':'catastro'}
    def tearDown(self):
        self.widget.controls_running=False
        self.widget.execution_status_timer.stop()
        self.widget.review_dirty=False
        self.widget.close()

    def test_confirmation_warns_and_counts_only_executable_rules(self):
        metadata=dict(self.widget.validation_confirmation_metadata(self.params,'pg_temp',[self.alpha,self.geo],None,self.report))
        self.assertEqual(metadata['Total de reglas'],'1')
        notice=metadata['Advertencia: validación sin GDB']
        self.assertIn('regla_geo',notice)
        self.assertIn('reporte general',notice)
        self.assertNotIn('regla_alpha',notice)

    def test_explicit_popup_appears_before_parameter_confirmation(self):
        events = []
        with patch.object(module.QMessageBox, 'warning', side_effect=lambda *args: events.append(('alerta', args[1], args[2]))), patch.object(module.QDialog, 'exec_', side_effect=lambda: events.append(('confirmacion',)) or module.QDialog.Rejected):
            accepted = self.widget.confirm_validation(self.params, 'pg_temp', [self.alpha, self.geo], None, self.report)
        self.assertFalse(accepted)
        self.assertEqual([event[0] for event in events], ['alerta', 'confirmacion'])
        self.assertIn('regla_geo', events[0][2])
        self.assertIn('reporte general', events[0][2])

    def test_no_popup_with_gdb_and_popup_without_spatial_rules(self):
        with patch.object(module.QMessageBox, 'warning') as warning, patch.object(module.QDialog, 'exec_', return_value=module.QDialog.Rejected):
            self.widget.confirm_validation(self.params, 'pg_temp', [self.alpha], None)
        warning.assert_called_once()
        self.assertIn('Ninguna de las reglas seleccionadas requiere GDB', warning.call_args.args[2])
        with patch.object(self.widget, 'active_cica_gdb', return_value=SimpleNamespace(filename='prueba.gdb')), patch.object(module.QMessageBox, 'warning') as warning, patch.object(module.QDialog, 'exec_', return_value=module.QDialog.Rejected):
            self.widget.confirm_validation(self.params, 'pg_temp', [self.alpha, self.geo], None, self.report)
        warning.assert_not_called()

    def test_worker_receives_only_alpha_rules_and_reports_record_omissions(self):
        with patch.object(self.widget,'connection_params',return_value=self.params),patch.object(self.widget,'confirm_validation',return_value=True),patch.object(self.widget,'confirm_review_changes',return_value=True),patch.object(self.widget,'resolve_validation_context',return_value='Municipio de prueba'),patch.object(module,'QThread'),patch.object(module,'RuleWorker') as worker:
            self.widget.run_rules()
        worker.assert_called_once()
        self.assertEqual(worker.call_args.args[4],[self.alpha])
        self.assertIsNone(worker.call_args.args[5])
        self.assertEqual(self.widget.general_report_error,'No ejecutado: requiere GDB.')
        self.assertEqual(self.widget.execution_info['Geodatabase CICA'], 'GDB no cargada')
        self.assertIn('regla_geo',self.widget.execution_info['Reglas no ejecutadas por falta de GDB'])
        sheet=Workbook().active
        prepare_validation_index(sheet,self.widget.execution_info,'Municipio de prueba')
        values=[cell.value for row in sheet for cell in row]
        self.assertIn('Reglas no ejecutadas por falta de GDB',values)
        self.assertIn('Fisicas · regla_geo',values)
        self.assertEqual(self.widget.progress.maximum(),1)

    def test_all_geographic_selection_does_not_start_or_destroy_previous_results(self):
        self.widget.category_checks['Administrativas'].setChecked(False)
        previous=module.RuleResult('anterior','Fisicas','Correcta',0)
        self.widget.results=[previous]
        with patch.object(module.QMessageBox,'warning') as warning,patch.object(module,'RuleWorker') as worker:
            self.widget.run_rules()
        warning.assert_called_once()
        worker.assert_not_called()
        self.assertEqual(self.widget.results,[previous])

    def test_cancel_confirmation_keeps_previous_execution_metadata(self):
        self.widget.execution_info={'Estado':'anterior'}
        with patch.object(self.widget,'connection_params',return_value=self.params),patch.object(self.widget,'confirm_validation',return_value=False),patch.object(module,'RuleWorker') as worker:
            self.widget.run_rules()
        worker.assert_not_called()
        self.assertEqual(self.widget.execution_info,{'Estado':'anterior'})
