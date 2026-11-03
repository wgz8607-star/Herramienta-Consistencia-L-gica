import unittest
from qgis_control_calidad.current_references import catalog_from_names, prepare_current_references


class ReferenceNamingTests(unittest.TestCase):
    def test_new_names_keep_latest_date_and_pair(self):
        rows, ignored = catalog_from_names([
            'r1_08421_20260930', 'r2_08421_20260930',
            'r1_08421_20250830', 'r1_13006_20260930',
            '08421_20260930_r1', 'r1_08421_20260230',
        ])
        self.assertEqual(rows[0]['divipola'], '08421')
        self.assertEqual(rows[0]['stamp'], '20260930')
        self.assertEqual(rows[0]['tables'], {'R1': 'r1_08421_20260930', 'R2': 'r2_08421_20260930'})
        self.assertEqual(rows[1]['tables'], {'R1': 'r1_13006_20260930'})
        self.assertEqual(set(ignored), {'08421_20260930_r1', 'r1_08421_20260230'})

    def test_selection_rejects_mismatched_table_before_connecting(self):
        selection = {'divipola': '08421', 'stamp': '20260930', 'tables': {'R1': 'r1_13006_20260930'}}
        with self.assertRaises(ValueError):
            prepare_current_references({}, selection, ['R1'])
