import unittest
from unittest.mock import MagicMock,patch
from qgis_control_calidad import dialog as module
from qgis_control_calidad.environment_availability import has_active_controls
from qgis_control_calidad.review import build_cases
from test_temporary_references import app,render


class AvailabilityTests(unittest.TestCase):
    def test_only_active_nonempty_controls_in_published_versions_enable_environment(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect=[(False,),(True,)]
        with patch('psycopg2.connect',return_value=connection):
            self.assertTrue(has_active_controls({}, {'kind':'tables','schema':'public','tables':['version1','version2']}))
        query=render(cursor.execute.call_args.args[0])
        for fragment in ("r.activa","r.tipo='CONTROL'",'version_publicada',"[^[:space:]]"):
            self.assertIn(fragment,query)
        connection.set_session.assert_called_once_with(readonly=True)
        connection.close.assert_called_once()
        self.assertFalse(has_active_controls({},None))

    def test_environment_hides_reappears_and_connection_errors_preserve_choices(self):
        widget=module.ControlCalidadDialog();self.addCleanup(widget.close)
        with patch.object(widget,'repository_connection_params',return_value={}),patch.object(widget,'repository_source',return_value={'kind':'tables'}),patch.object(widget,'report_task',side_effect=lambda fn,*args:fn(*args)):
            with patch.object(module,'has_active_controls',return_value=False):widget.refresh_environment_choices()
            self.assertEqual(widget.environment.findText('Validaciones de consistencia lógica'),-1)
            self.assertGreaterEqual(widget.environment.findText(module.SNC_ENVIRONMENT),0)
            with patch.object(module,'has_active_controls',return_value=True):widget.refresh_environment_choices()
            self.assertGreaterEqual(widget.environment.findText('Validaciones de consistencia lógica'),0)
            choices=[widget.environment.itemText(i) for i in range(widget.environment.count())]
            with patch.object(module,'has_active_controls',side_effect=RuntimeError('sin conexión')):widget.refresh_environment_choices()
            self.assertEqual([widget.environment.itemText(i) for i in range(widget.environment.count())],choices)
            self.assertIn('No se pudo verificar',widget.status.text())

    def test_structure_stays_in_results_but_not_in_exception_controls(self):
        widget=module.ControlCalidadDialog();self.addCleanup(widget.close)
        widget.results=[module.RuleResult('struct_01','Estructura','Correcta',1,rows=[{'numero_predial':'00001'}]),module.RuleResult('regla_1','Administrativas','Correcta',1,rows=[{'numero_predial':'00002'}])]
        widget.review_cases=build_cases(widget.results,{})
        widget.refresh_detail_review_controls()
        self.assertNotIn('Estructura',widget.detail_review_rows)
        self.assertIn('Administrativas',widget.detail_review_rows)
        self.assertTrue(any(widget.table.item(i,0).text()=='Estructura' for i in range(widget.table.rowCount())))
        with patch.object(module.QFileDialog,'getOpenFileName') as picker:widget.recover_detail('Estructura')
        picker.assert_not_called()
