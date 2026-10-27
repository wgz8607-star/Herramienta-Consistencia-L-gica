import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from qgis_control_calidad.review_files import fingerprint_file, inspect_source


class ReviewFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'file.xlsx'
        self.path.write_bytes(b'original')
        snapshot = fingerprint_file(self.path)
        self.source = {'path': str(self.path), 'file_snapshot': snapshot,
                       'observed_stat': snapshot['stat'], 'file_state': 'current'}

    def test_unchanged_touch_and_changed_content(self):
        self.assertIsNone(inspect_source(self.source))
        os.utime(self.path, (1, 1))
        self.assertIsNone(inspect_source(self.source))
        self.path.write_bytes(b'modified')
        self.assertIsNotNone(inspect_source(self.source))
        self.assertEqual(self.source['file_state'], 'modified')
        self.path.write_bytes(b'original')
        self.assertIsNone(inspect_source(self.source, force=True))
        self.assertEqual(self.source['file_state'], 'current')

    def test_missing_file_keeps_snapshot_for_recovery(self):
        snapshot = self.source['file_snapshot'].copy()
        self.path.unlink()
        self.assertIsNotNone(inspect_source(self.source))
        self.assertEqual(self.source['file_state'], 'unavailable')
        self.assertEqual(self.source['file_snapshot'], snapshot)

    def test_export_force_hash_detects_change_even_if_metadata_is_cached(self):
        cached = self.source['observed_stat']
        self.path.write_bytes(b'modified')
        with patch('qgis_control_calidad.review_files.file_stat', return_value=cached):
            self.assertIsNone(inspect_source(self.source))
            self.assertIsNotNone(inspect_source(self.source, force=True))

    def test_changing_during_fingerprint_is_rejected(self):
        with patch('qgis_control_calidad.review_files.file_stat', side_effect=[(1, 1, 1, 1), (2, 2, 2, 2)]):
            with self.assertRaises(ValueError):
                fingerprint_file(self.path)
