import unittest
from unittest.mock import patch
from qgis_control_calidad.cica_progress import CicaProgressDialog
from test_temporary_references import app


class CicaProgressRemainderTests(unittest.TestCase):
    def make_dialog(self,data=None,loader=lambda:{}):
        with patch('qgis_control_calidad.cica_progress.QTimer.singleShot'):
            dialog=CicaProgressDialog(loader)
        self.addCleanup(dialog.close)
        dialog.set_data(data or {'rows':[]})
        return dialog

    def source(self):
        return {'rows':[
            ('08421','Urbano','01','ASIGNADO',80,75,5,0),
            ('08421','Urbano','01','VALIDADO',20,15,5,0),
            ('08421','Rural','00','CONTROL_CALIDAD_GENERAL',40,35,5,0)],
            'recognition_stages':('VALIDADO',),
            'quality_stages':('VALIDADO','CONTROL_CALIDAD_GENERAL')}

    def test_each_state_has_its_own_remaining_count_and_separate_section(self):
        dialog=self.make_dialog(self.source())
        expected={('recognition','active'):110,('recognition','cancelled'):10,('quality','active'):75,('quality','cancelled'):5}
        for key,remaining in expected.items():
            self.assertEqual(dialog.remaining_widgets[key].text(),f'Faltan {remaining} predios para el 100 %')
        for metrics in dialog.metric_widgets.values():
            for bar,value,role in metrics:
                self.assertTrue(dialog.metric_sections[role].isAncestorOf(bar))
                other='cancelled' if role=='active' else 'active'
                self.assertFalse(dialog.metric_sections[other].isAncestorOf(bar))

    def test_cancelled_bar_uses_cancelled_total_in_both_display_modes(self):
        dialog=self.make_dialog({'rows':[
            ('08421','Urbano','01','VALIDADO',30930,30000,930,0),
            ('08421','Urbano','01','ASIGNADO',963,0,963,0)],
            'recognition_stages':('VALIDADO',),'quality_stages':('VALIDADO',)})
        for mode in ('Cantidad','Porcentaje'):
            dialog.mode.setCurrentText(mode)
            for key in ('recognition','quality'):
                bar,value,role=dialog.metric_widgets[key][1]
                self.assertEqual(bar.value(),491)
                self.assertIn('930 | 49.1 %',value.text())
                self.assertEqual(dialog.remaining_widgets[(key,'cancelled')].text(),'Faltan 963 predios para el 100 %')
                self.assertEqual(dialog.metric_widgets[key][0][0].value(),1000)
        dialog.set_data({'rows':[('08421','Urbano','01','VALIDADO',10,0,10,0)],'recognition_stages':('VALIDADO',),'quality_stages':('VALIDADO',)})
        self.assertEqual(dialog.metric_widgets['recognition'][1][0].value(),1000)
        self.assertEqual(dialog.metric_widgets['recognition'][0][0].value(),0)

    def test_remaining_counts_follow_zone_combinations_and_mode(self):
        dialog=self.make_dialog(self.source());dialog.toggle_zone('Urbano')
        self.assertEqual(dialog.remaining_widgets[('recognition','active')].text(),'Faltan 75 predios para el 100 %')
        self.assertEqual(dialog.remaining_widgets[('quality','cancelled')].text(),'Faltan 5 predios para el 100 %')
        dialog.toggle_zone('Rural')
        self.assertEqual(dialog.remaining_widgets[('recognition','active')].text(),'Faltan 110 predios para el 100 %')
        dialog.mode.setCurrentText('Porcentaje')
        self.assertEqual(dialog.remaining_widgets[('recognition','active')].text(),'Faltan 110 predios para el 100 %')

    def test_empty_selection_and_unavailable_indicators_do_not_invent_progress(self):
        dialog=self.make_dialog({'rows':[],'recognition_stages':('VALIDADO',)})
        self.assertIn('Sin predios activos',dialog.remaining_widgets[('recognition','active')].text())
        self.assertIn('Sin predios cancelados',dialog.remaining_widgets[('recognition','cancelled')].text())
        dialog.set_data({'rows':[]})
        self.assertEqual(dialog.remaining_widgets[('recognition','active')].text(),'Pendiente de calcular')

    def test_load_failure_clears_previous_remaining_values(self):
        dialog=self.make_dialog(self.source(),loader=lambda:(_ for _ in ()).throw(RuntimeError('sin acceso')))
        with patch('qgis_control_calidad.cica_progress.QMessageBox.warning'):
            dialog.load()
        self.assertTrue(all(label.text()=='—' for label in dialog.remaining_widgets.values()))
