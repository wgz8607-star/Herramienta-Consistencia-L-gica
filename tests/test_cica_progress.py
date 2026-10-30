import unittest
from unittest.mock import patch
from qgis_control_calidad.cica_progress import CicaProgressDialog
from qgis_control_calidad.dialog import ControlCalidadDialog
from qgis_control_calidad.territorial_statistics import statistics_from_values
from qgis_control_calidad.territorial_filter import TerritorialOverview
from test_temporary_references import app

U = '08421010000010001'
R = '08421000000010001'
C = '08421020000010001'


class AppliedFilterOverviewTests(unittest.TestCase):
    def test_main_summary_counts_applied_scope_and_prefix_without_changing_baseline(self):
        widget = ControlCalidadDialog(); self.addCleanup(widget.close)
        source = statistics_from_values([U, U, R, C], source='Base de ejemplo')
        r1 = statistics_from_values([U, U, R], source='R1 de ejemplo', unique=True)
        widget.filter_statistics = {'source_statistics': source, 'r1_statistics': r1}
        widget.apply_advanced_filter('urban', ())
        self.assertEqual(widget.filter_overview.total_labels['source'].text(), '2')
        self.assertEqual(widget.filter_overview.total_labels['r1'].text(), '1')
        self.assertEqual(widget.filter_overview.rows['rural'].text(1), '0')
        self.assertIn('de 4 disponibles', widget.filter_overview.coverage_labels['source'].text())
        self.assertIn('Alcance a validar: Urbano', widget.advanced_filter_summary.text())
        widget.apply_advanced_filter('rural', (R,))
        self.assertEqual(widget.filter_overview.rows['total'].text(1), '1')
        self.assertEqual(widget.filter_overview.rows['urban'].text(1), '0')
        widget.filter_overview.set_statistics(widget.filter_statistics)
        self.assertEqual(widget.filter_overview.rows['total'].text(1), '1')
        self.assertEqual(source['total'], 4)
        self.assertEqual(r1['total'], 2)
        widget.apply_advanced_filter('all', ())
        self.assertEqual(widget.filter_overview.rows['total'].text(1), '4')
        self.assertEqual(widget.filter_overview.rows['total'].text(2), '2')
        popup = TerritorialOverview(); self.addCleanup(popup.close)
        popup.set_statistics(widget.filter_statistics)
        self.assertEqual(popup.rows['total'].text(1), '4')


class CicaProgressTests(unittest.TestCase):
    def make_dialog(self, loader=lambda: {}):
        with patch('qgis_control_calidad.cica_progress.QTimer.singleShot'):
            dialog = CicaProgressDialog(loader)
        self.addCleanup(dialog.close)
        return dialog

    def test_zone_and_cp_codes_change_report_only(self):
        data = {'municipality_label': 'LURUACO, ATLÁNTICO (08421)', 'source': 'sentencias.snc_cica_copy.cica_predio', 'rows': [
            ('08421', 'Urbano', '01', 'ASIGNADO', 10, 8, 2, 0),
            ('08421', 'Centro poblado', '02', 'TRAMITADO', 7, 5, 1, 1),
            ('08421', 'Centro poblado', '03', 'CONTROL_CALIDAD_GENERAL', 4, 2, 2, 0),
            ('08421', 'Rural', '00', 'ASIGNADO', 6, 4, 2, 0)]}
        dialog = self.make_dialog()
        dialog.set_data(data)
        self.assertEqual(dialog.values['total'].text(), '27')
        dialog.set_zone('Centro poblado')
        self.assertEqual(dialog.values['total'].text(), '11')
        self.assertEqual([dialog.cp.itemData(i) for i in range(dialog.cp.count())], ['', '02', '03'])
        dialog.cp.setCurrentIndex(dialog.cp.findData('02'))
        self.assertEqual(dialog.values['total'].text(), '7')
        self.assertEqual(dialog.values['active'].text(), '5')
        self.assertEqual(dialog.values['cancelled'].text(), '1')
        self.assertEqual(dialog.table.topLevelItemCount(), 1)
        dialog.mode.setCurrentText('Porcentaje')
        self.assertEqual(dialog.values['total'].text(), '7')
        dialog.set_zone('Urbano')
        self.assertEqual(dialog.values['total'].text(), '10')
        self.assertTrue(dialog.cp.isHidden())
        self.assertEqual(len(data['rows']), 4)

    def test_report_button_is_cica_only_and_above_statistics_button(self):
        widget = ControlCalidadDialog(); self.addCleanup(widget.close)
        self.assertTrue(widget.cica_progress_button.isHidden())
        widget.model.setCurrentText('CICA')
        self.assertFalse(widget.cica_progress_button.isHidden())
        layout = widget.cica_progress_button.parentWidget().layout()
        self.assertLess(layout.indexOf(widget.cica_progress_button), layout.indexOf(widget.open_filter_window_button))
        widget.scope_selection = 'urban'
        with patch('qgis_control_calidad.cica_progress.CicaProgressDialog') as factory:
            widget.open_cica_progress()
        factory.assert_called_once_with(widget.read_cica_progress_data, widget)
        self.assertEqual(widget.scope_selection, 'urban')
        widget.model.setCurrentIndex(0)
        self.assertTrue(widget.cica_progress_button.isHidden())

    def test_failed_refresh_clears_stale_counts(self):
        def failure(): raise RuntimeError('Sin acceso')
        dialog = self.make_dialog(failure)
        dialog.set_data({'rows': [('08421', 'Urbano', '01', 'ASIGNADO', 10, 8, 2, 0)]})
        with patch('qgis_control_calidad.cica_progress.QMessageBox.warning'):
            dialog.load()
        self.assertEqual(dialog.values['total'].text(), '—')
        self.assertEqual(dialog.rows, [])
        self.assertIn('Sin acceso', dialog.origin.text())
        self.assertFalse(dialog.reading)

    def test_file_report_is_independent_of_r1_and_validation_scope(self):
        import tempfile
        from pathlib import Path
        from qgis_control_calidad.cica_data import prepare_csv
        widget = ControlCalidadDialog(); self.addCleanup(widget.close)
        widget.model.setCurrentText('CICA')
        widget.scope_selection = 'urban'; widget.scope_prefixes = (U,)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'predio.csv'
            source.write_text('numero_predial;estado;etapa\n0842101000001;ACTIVO;ASIGNADO\n0842100000001;CANCELADO;TRAMITADO\n')
            ref = prepare_csv('cica_predio', source); widget.cica_references['cica_predio'] = ref
            widget.update_advanced_filter_availability()
            widget.apply_advanced_filter('urban', (U,))
            with patch.object(widget, 'repository_connection_params') as repository:
                data = widget.read_cica_progress_data()
            repository.assert_not_called()
            self.assertEqual(sum(row[4] for row in data['rows']), 2)
            self.assertIn('LURUACO', data['municipality_label'])
            self.assertEqual((widget.scope_selection, widget.scope_prefixes), ('urban', (U,)))
            self.assertFalse(widget.filter_reading)
            self.assertTrue(widget.main_tabs.isEnabled())
            ref.close();widget.cica_references = {}

    def test_failed_report_lookup_restores_main_controls(self):
        from types import SimpleNamespace
        widget = ControlCalidadDialog(); self.addCleanup(widget.close)
        widget.model.setCurrentText('CICA')
        widget.cica_references['cica_predio'] = SimpleNamespace(close=lambda: None)
        widget.cica_selection = {'municipality': '08421', 'stages': ('ASIGNADO',)}
        with patch.object(widget, 'repository_connection_params', return_value={'dbname': 'sentencias'}), \
             patch.object(widget, 'report_task', side_effect=RuntimeError('Sin acceso')):
            with self.assertRaisesRegex(RuntimeError, 'Sin acceso'):
                widget.read_cica_progress_data()
        self.assertFalse(widget.filter_reading)
        self.assertTrue(widget.main_tabs.isEnabled())

    def test_dashboard_uses_only_configured_indicators_and_keeps_snc_at_bottom(self):
        dialog = self.make_dialog()
        rows = [('08421', 'Centro poblado', '02', 'CONTROL_CALIDAD_GENERAL', 3, 2, 1, 0),
                ('08421', 'Centro poblado', '02', 'TRAMITADO', 2, 1, 1, 0),
                ('08421', 'Centro poblado', '02', 'ASIGNADO', 1, 1, 0, 0)]
        dialog.set_data({'rows': rows})
        self.assertEqual(set(dialog.values), {'total', 'active', 'cancelled'})
        self.assertEqual(dialog.metric_widgets['recognition'][0][1].text(), '—')
        self.assertEqual(dialog.no_areas.text(), '—')
        self.assertEqual(dialog.snc.text(), '—')
        dialog.set_data({'rows': rows, 'recognition_stages': ('CONTROL_CALIDAD_GENERAL', 'TRAMITADO'),
                         'snc_stages': ('TRAMITADO',), 'with_areas_rows': [('08421', 'Centro poblado', '02', 3)]})
        dialog.set_zone('Centro poblado')
        self.assertIn('3 | 75.0 %', dialog.metric_widgets['recognition'][0][1].text())
        self.assertIn('2 | 50.0 %', dialog.metric_widgets['quality'][0][1].text())
        self.assertEqual(dialog.no_areas.text(), '1')
        self.assertEqual(dialog.snc.text(), '2')
        dialog.select_cp('02');dialog.select_cp('02')
        self.assertTrue(dialog.cp_buttons['02'].isChecked())

    def test_npn_detail_from_file_preserves_zeroes_and_selected_cp(self):
        import tempfile
        from pathlib import Path
        from qgis_control_calidad.cica_data import prepare_csv
        from qgis_control_calidad.territorial_statistics import cica_predio_details_from_snapshot
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'predio.csv'
            source.write_text('numero_predial;estado;etapa\n0842102000001;ACTIVO;ASIGNADO\n0842102000001;ACTIVO;ASIGNADO\n0842103000001;CANCELADO;TRAMITADO\n')
            ref = prepare_csv('cica_predio', source)
            try:
                detail = cica_predio_details_from_snapshot(ref, 'Centro poblado', '02')
                self.assertEqual(detail['rows'], [('0842102000001', 'ASIGNADO', 'ACTIVO', 2)])
                self.assertFalse(detail['has_more'])
            finally:
                ref.close()
