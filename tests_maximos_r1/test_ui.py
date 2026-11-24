import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch
from qgis.core import QgsApplication
from validador_renumeracion.dialog import MaximaDialog
from validador_renumeracion.core import build_maxima
from validador_renumeracion import classFactory
from test_maximos import npn

app=QgsApplication.instance() or QgsApplication([],False);app.initQgis()


class MaximaUiTests(unittest.TestCase):
    def setUp(self):
        self.dialog=MaximaDialog();self.addCleanup(self.dialog.close)
    def test_three_sources_and_loaded_maxima_can_be_filtered_and_cleared(self):
        self.assertEqual(self.dialog.source_mode.count(),3)
        result=build_maxima([(2,npn()),(3,npn(zone='02')),(4,npn(municipality='25377'))])
        self.dialog.set_result(result,'Origen de prueba')
        self.assertEqual(self.dialog.views['Por zona-sector'].topLevelItemCount(),3)
        self.dialog.municipality.setCurrentIndex(self.dialog.municipality.findData('41020'))
        self.dialog.zone.setCurrentIndex(self.dialog.zone.findData('0201'))
        self.assertEqual(self.dialog.views['Por zona-sector'].topLevelItemCount(),1)
        self.assertTrue(self.dialog.export_button.isEnabled())
        self.dialog.source_mode.setCurrentIndex(1)
        self.assertIsNone(self.dialog.result)
        self.assertFalse(self.dialog.export_button.isEnabled())
        self.assertEqual(self.dialog.schema_label.text(),'r1_r2')
        self.dialog.source_mode.setCurrentIndex(2)
        self.assertEqual(self.dialog.schema_label.text(),'public')
    def test_preloaded_uses_latest_per_municipality_and_displays_date(self):
        self.dialog.source_mode.setCurrentIndex(1)
        rows=[('r1_41020_20260930','numero_predial'),('r1_41020_20261031','numero_predial'),('r1_25377_20261031','numero_predial')]
        with patch.object(self.dialog,'reference_params',return_value={'dbname':'sentencias'}),patch('validador_renumeracion.dialog.list_tables',return_value=rows):
            self.dialog.read_tables()
        self.assertEqual(self.dialog.tables.count(),2)
        self.dialog.tables.setCurrentIndex(1)
        self.assertEqual(self.dialog.tables.currentData()[0],'r1_41020_20261031')
        self.assertIn('31/10/2026',self.dialog.source_mode.itemText(1))
        self.dialog.source_mode.setCurrentIndex(2)
        self.assertIn('Sin fecha seleccionada',self.dialog.source_mode.itemText(1))

    def test_preloaded_database_is_sentencias_public_keeps_selected_database(self):
        from qgis.core import QgsSettings
        settings=QgsSettings();group='PostgreSQL/connections/maximos_test/'
        for key,value in {'host':'localhost','database':'catastro_test','username':'reader','password':'test'}.items():settings.setValue(group+key,value)
        try:
            self.dialog.refresh_connections();self.dialog.connection.setCurrentText('maximos_test')
            self.dialog.source_mode.setCurrentIndex(1)
            self.assertEqual(self.dialog.params()['dbname'],'sentencias')
            self.dialog.source_mode.setCurrentIndex(2)
            self.assertEqual(self.dialog.params()['dbname'],'catastro_test')
        finally:settings.remove('PostgreSQL/connections/maximos_test')

    def test_invalid_new_workbook_cannot_reuse_previous_column_selection(self):
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'sin_npn.xlsx';book=Workbook();book.active.append(['Sin dato predial']);book.save(path);book.close()
            self.dialog.column.addItem('Columna anterior',2)
            with patch('validador_renumeracion.dialog.QFileDialog.getOpenFileName',return_value=(str(path),'')),patch('validador_renumeracion.dialog.QMessageBox.warning'):
                self.dialog.choose_file()
            self.assertIsNone(self.dialog.column.currentData())
            self.assertIsNone(self.dialog.result)

    def test_background_task_restores_controls_on_error(self):
        with self.assertRaises(RuntimeError):self.dialog.task(lambda:(_ for _ in ()).throw(RuntimeError('error de prueba')))
        self.assertFalse(self.dialog.busy)
        self.assertTrue(self.dialog.inputs.isEnabled())
    def test_plugin_entrypoint_is_independent(self):
        plugin=classFactory(object())
        self.assertEqual(plugin.__class__.__module__,'validador_renumeracion.plugin')

    def test_plugin_opens_source_selection_before_r1(self):
        from unittest.mock import MagicMock
        from qgis.PyQt.QtWidgets import QWidget
        from validador_renumeracion.candidate_dialog import CandidateDialog
        window=QWidget();iface=MagicMock();iface.mainWindow.return_value=window
        plugin=classFactory(iface);plugin.initGui()
        try:
            plugin.action.trigger();app.processEvents()
            self.assertIsInstance(plugin.dialog,CandidateDialog)
            self.assertTrue(plugin.dialog.isVisible())
            self.assertFalse(plugin.reference_dialog.isVisible())
            plugin.dialog.r1_button.click();app.processEvents()
            self.assertTrue(plugin.reference_dialog.isVisible())
        finally:plugin.unload();window.close()

    def test_maxima_uses_repository_or_selected_source_without_qgis_selector(self):
        self.assertTrue(self.dialog.connection_controls.isHidden())
        self.dialog.source_mode.setCurrentIndex(1)
        with patch('validador_renumeracion.repository.repository_params',return_value={'dbname':'sentencias'}):
            self.assertEqual(self.dialog.reference_params(),{'dbname':'sentencias'})
        self.dialog.source_mode.setCurrentIndex(2)
        self.dialog.selected_source_params={'dbname':'modelo_seleccionado'}
        self.assertEqual(self.dialog.reference_params()['dbname'],'modelo_seleccionado')
