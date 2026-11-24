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
        self.assertEqual(self.dialog.views['Por zona'].topLevelItemCount(),3)
        self.dialog.municipality.setCurrentIndex(self.dialog.municipality.findData('41020'))
        self.dialog.zone.setCurrentIndex(self.dialog.zone.findData('02'))
        self.assertEqual(self.dialog.views['Por zona'].topLevelItemCount(),1)
        self.assertTrue(self.dialog.export_button.isEnabled())
        self.dialog.source_mode.setCurrentIndex(1)
        self.assertIsNone(self.dialog.result)
        self.assertFalse(self.dialog.export_button.isEnabled())
        self.assertEqual(self.dialog.schema_label.text(),'r1_r2')
        self.dialog.source_mode.setCurrentIndex(2)
        self.assertEqual(self.dialog.schema_label.text(),'public')
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
