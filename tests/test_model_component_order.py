import unittest
from qgis_control_calidad.dialog import ControlCalidadDialog, RuleResult
from test_temporary_references import app


class ModelComponentOrderTests(unittest.TestCase):
    def setUp(self):
        self.widget = ControlCalidadDialog(); self.addCleanup(self.widget.close)
        self.names = ['Económicas', 'Novedades', 'Jurídicas', 'Étnico', 'Administrativas', 'Físicas', 'Estructura']
        self.widget.results = [RuleResult('regla_' + str(index), name, 'Correcta', index + 1) for index, name in enumerate(self.names)]
        self.widget.review_cases = []

    def test_model_results_have_requested_order_and_numbers_with_total_last(self):
        self.widget.execution_info = {'Ambiente': 'Validaciones del modelo'}
        self.widget.refresh_review_statistics()
        table = self.widget.table
        self.assertEqual([table.item(i, 0).text() for i in range(table.rowCount())],
                         ['Estructura', 'Administrativas', 'Jurídicas', 'Físicas', 'Económicas', 'Novedades', 'Étnico', 'TOTAL'])
        self.assertEqual([table.verticalHeaderItem(i).text() for i in range(table.rowCount())], ['0', '1', '2', '3', '4', '5', '9', 'Σ'])
        self.assertEqual(table.item(7, 2).text(), '28')
        self.assertEqual(table.item(7, 1).text(), '7')

    def test_cargue_environment_keeps_its_existing_order(self):
        self.widget.execution_info = {'Ambiente': 'Validaciones para cargue a SNC'}
        self.widget.refresh_review_statistics()
        self.assertEqual([self.widget.table.item(i, 0).text() for i in range(7)], sorted(self.names))
        self.assertIsNone(self.widget.table.verticalHeaderItem(0))
