import csv
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from osgeo import ogr, osr
from qgis.PyQt.QtWidgets import QLineEdit, QMessageBox
from qgis_control_calidad.cica_gdb import prepare_gdb, install_gdb
from qgis_control_calidad.cica_data import resolve_csv_tables
from qgis_control_calidad.ingestion import CicaIngestionDialog
from qgis_control_calidad import dialog as module
from test_cica_and_formats import CicaConnection
from test_temporary_references import render


class CicaGdbTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'entrada.gdb'
        driver = ogr.GetDriverByName('OpenFileGDB')
        if not driver or driver.GetMetadataItem('DCAP_CREATE') != 'YES':
            self.skipTest('Se requiere GDAL con escritura OpenFileGDB para crear la prueba.')
        dataset = driver.CreateDataSource(str(self.source))
        srs = osr.SpatialReference(); srs.ImportFromEPSG(4326)
        layer = dataset.CreateLayer('cica_terreno', srs, ogr.wkbPolygon)
        layer.CreateField(ogr.FieldDefn('Numero_Predial', ogr.OFTString))
        layer.CreateField(ogr.FieldDefn('Area', ogr.OFTReal))
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('Numero_Predial', '00001'); feature.SetField('Area', 1.25)
        feature.SetGeometry(ogr.CreateGeometryFromWkt('POLYGON ((0 0,1 0,1 1,0 0))'))
        self.assertEqual(layer.CreateFeature(feature), ogr.OGRERR_NONE)
        feature = None; layer = None; dataset = None

    def prepared(self, source=None):
        result = prepare_gdb(source or self.source)
        self.addCleanup(result.close)
        return result

    def test_gdb_snapshot_preserves_geometry_epsg_attributes_and_leaves_source_unchanged(self):
        before = {str(p.relative_to(self.source)): p.read_bytes() for p in self.source.rglob('*') if p.is_file()}
        prepared = self.prepared()
        layer = prepared.layers['cica_terreno']
        self.assertEqual(layer.geometry_column, 'geom')
        self.assertEqual(layer.types[layer.columns.index('geom')], 'geometry')
        self.assertEqual(layer.srid, 4326)
        self.assertEqual(layer.row_count, 1)
        with layer.csv_path.open(encoding='utf-8', newline='') as stream:
            row = next(csv.reader(stream))
        self.assertEqual(row[layer.columns.index('numero_predial')], '00001')
        self.assertEqual(row[layer.columns.index('area')], '1.25')
        ewkt = row[layer.columns.index(layer.geometry_column)]
        self.assertTrue(ewkt.startswith('SRID=4326;'))
        geometry = ogr.CreateGeometryFromWkt(ewkt.split(';', 1)[1])
        self.assertAlmostEqual(geometry.GetArea(), 0.5)
        self.assertEqual(before, {str(p.relative_to(self.source)): p.read_bytes() for p in self.source.rglob('*') if p.is_file()})
        prepared.close(); self.assertFalse(layer.csv_path.exists())
        self.assertTrue(self.source.exists())

    def test_all_spatial_layers_use_geom_and_keep_nonspatial_tables_without_geometry(self):
        dataset = ogr.Open(str(self.source), 1)
        srs = osr.SpatialReference(); srs.ImportFromEPSG(9377)
        for name, kind, wkt in (
            ('u_construccion', ogr.wkbMultiPolygon, 'MULTIPOLYGON (((0 0,2 0,2 2,0 0)))'),
            ('puntos', ogr.wkbPoint, 'POINT (4 5)'),
            ('lineas', ogr.wkbLineString, 'LINESTRING (0 0,1 1)'),
        ):
            layer = dataset.CreateLayer(name, srs, kind, options=['GEOMETRY_NAME=Shape'])
            layer.CreateField(ogr.FieldDefn('geom', ogr.OFTString))
            layer.CreateField(ogr.FieldDefn('geom_atributo', ogr.OFTString))
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField('geom', 'atributo original')
            feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
            self.assertEqual(layer.CreateFeature(feature), ogr.OGRERR_NONE)
            feature = None; layer = None
        layer = dataset.CreateLayer('tabla_sin_geometria', geom_type=ogr.wkbNone)
        layer.CreateField(ogr.FieldDefn('codigo', ogr.OFTString))
        layer = None; dataset = None
        prepared = self.prepared()
        for name in ('u_construccion', 'puntos', 'lineas'):
            layer = prepared.layers[name]
            self.assertEqual(layer.geometry_column, 'geom')
            self.assertEqual(layer.srid, 9377)
            with layer.csv_path.open(encoding='utf-8', newline='') as stream:
                row = next(csv.reader(stream))
            self.assertEqual(row[layer.columns.index('geom_atributo_2')], 'atributo original')
            geometry = ogr.CreateGeometryFromWkt(row[layer.columns.index('geom')].split(';', 1)[1])
            self.assertIsNotNone(geometry)
            if name == 'u_construccion':
                self.assertEqual(geometry.GetGeometryName(), 'MULTIPOLYGON')
                self.assertAlmostEqual(geometry.GetArea(), 2)
        self.assertEqual(prepared.layers['tabla_sin_geometria'].geometry_column, '')

    def test_gdb_menu_opens_zip_or_folder_picker_directly(self):
        dialog = CicaIngestionDialog()
        try:
            self.assertEqual(len(dialog.gdb_source_menu.actions()), 2)
            with patch('qgis_control_calidad.ingestion.QFileDialog.getOpenFileName', return_value=('', '')) as zip_picker, patch('qgis_control_calidad.ingestion.QFileDialog.getExistingDirectory', return_value='') as folder_picker:
                dialog.gdb_source_menu.actions()[0].trigger()
                zip_picker.assert_called_once()
                folder_picker.assert_not_called()
                dialog.gdb_source_menu.actions()[1].trigger()
                folder_picker.assert_called_once()
        finally:
            dialog.close()

    def test_gdb_reports_layer_progress(self):
        events = []
        prepared = prepare_gdb(self.source, progress=lambda *args: events.append(args))
        self.addCleanup(prepared.close)
        self.assertEqual(events[0][:2], (0, 0))
        self.assertEqual(events[-1][:2], (1, 1))
        self.assertIn('cica_terreno', events[-1][2])

    def test_zipped_geodatabase_is_read_then_extracted_files_are_cleaned(self):
        path = Path(self.temp.name) / 'entrada.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            for file in self.source.rglob('*'):
                if file.is_file():
                    archive.write(file, Path('carpeta') / file.relative_to(self.source.parent))
        prepared = self.prepared(path)
        self.assertIn('cica_terreno', prepared.layers)
        root = Path(prepared.directory.name)
        prepared.close(); self.assertFalse(root.exists())
        self.assertTrue(path.exists())

    def test_zip_with_external_path_is_rejected(self):
        path = Path(self.temp.name) / 'incorrecto.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('../fuera.txt', 'no')
        with self.assertRaises(ValueError):
            prepare_gdb(path)
        self.assertFalse((Path(self.temp.name) / 'fuera.txt').exists())

    def test_gdb_install_uses_temp_tables_geometry_type_and_same_session(self):
        prepared = self.prepared()
        connection = CicaConnection()
        with patch('psycopg2.sql.Composed.as_string', lambda self, context: render(self)):
            install_gdb(connection, prepared)
        statements = [event[1] for event in connection.events if event[0] == 'sql']
        self.assertEqual(len(statements), 1)
        self.assertIn('CREATE TEMP TABLE "cica_terreno"', statements[0])
        self.assertIn('"geom" geometry', statements[0])
        self.assertIn('ON COMMIT PRESERVE ROWS', statements[0])
        worker = module.RuleWorker({}, 'test', '', '', [('Fisicas', 'r1', 'SELECT * FROM {esquema}.cica_terreno', '')], cica_gdb=prepared)
        worker_connection = CicaConnection()
        results = []; worker.result.connect(results.append)
        with patch.object(module.psycopg2, 'connect', return_value=worker_connection), patch('psycopg2.sql.Composed.as_string', lambda self, context: render(self)):
            worker.run()
        self.assertEqual(results[0].status, 'Correcta')
        self.assertIn(('sql', 'SELECT * FROM pg_temp.cica_terreno'), worker_connection.events)
        self.assertTrue(worker_connection.closed)
        self.assertFalse(worker_connection.tables)
        self.assertTrue(prepared.layers['cica_terreno'].csv_path.exists())

    def test_dialog_uses_current_label_and_no_destination_schema(self):
        prepared = self.prepared()
        dialog = CicaIngestionDialog(geodatabase=prepared)
        self.assertEqual(dialog.windowTitle(), 'Seleccionar fuente de datos CICA')
        self.assertFalse(hasattr(dialog, 'schema'))
        dialog.validate_inputs()
        self.assertEqual(dialog.result(), dialog.Accepted)
        dialog.clear_prepared()
        self.assertTrue(prepared.layers['cica_terreno'].csv_path.exists())

    def test_cancel_closes_new_gdb_and_does_not_discard_existing_one(self):
        original = self.prepared()
        replacement = self.prepared()
        dialog = CicaIngestionDialog(geodatabase=original)
        dialog.prepared_gdb = replacement
        dialog.reject(); dialog.clear_prepared()
        self.assertFalse(replacement.layers['cica_terreno'].csv_path.exists())
        self.assertTrue(original.layers['cica_terreno'].csv_path.exists())

    def test_windows_zip_directory_markers_and_no_recursive_binary_scan(self):
        path = Path(self.temp.name) / 'windows.gdb.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('carpeta\\entrada.gdb\\', '')
            for file in self.source.iterdir():
                if file.is_file():
                    archive.write(file, 'carpeta\\entrada.gdb\\' + file.name)
        # Reproduce Windows builds rejecting scandir on FileGDB binary files.
        # Finding the GDB root must not recurse through those files at all.
        with patch.object(Path, 'rglob', side_effect=OSError(267, 'El nombre del directorio no es válido')):
            prepared = self.prepared(path)
        self.assertEqual(prepared.layers['cica_terreno'].row_count, 1)
        self.assertEqual(prepared.layers['cica_terreno'].srid, 4326)

    def test_windows_traversal_and_multiple_gdb_roots_are_rejected(self):
        for name, entries in [('windows_escape.zip', ['..\\escape.gdb\\a.gdbtable']),
                              ('many.zip', ['one.gdb/a.gdbtable', 'two.gdb/b.gdbtable'])]:
            path = Path(self.temp.name) / name
            with zipfile.ZipFile(path, 'w') as archive:
                for entry in entries:
                    archive.writestr(entry, 'test')
            with self.assertRaises(ValueError):
                prepare_gdb(path)
        self.assertFalse((Path(self.temp.name) / 'escape.gdb').exists())

    def test_snc_source_hides_gdb_and_ignores_previously_loaded_gdb(self):
        prepared = self.prepared()
        dialog = CicaIngestionDialog(geodatabase=prepared, allow_gdb=False)
        self.assertTrue(dialog.gdb_card.isHidden())
        self.assertIsNone(dialog.existing_gdb)
        with patch('qgis_control_calidad.ingestion.QFileDialog.getOpenFileName') as picker:
            dialog.choose_gdb()
        picker.assert_not_called()
        with patch('qgis_control_calidad.ingestion.QMessageBox.warning'):
            dialog.validate_inputs()
        self.assertNotEqual(dialog.result(), dialog.Accepted)
        dialog.clear_prepared(); dialog.close()
        self.assertTrue(prepared.layers['cica_terreno'].csv_path.exists())

    def test_main_snc_omits_gdb_from_inputs_and_confirmation_but_preserves_it(self):
        prepared = self.prepared()
        widget = module.ControlCalidadDialog()
        self.addCleanup(widget.close)
        widget.model.setCurrentText('CICA')
        widget.cica_gdb = prepared
        widget.environment.blockSignals(True)
        widget.environment.setCurrentText(module.SNC_ENVIRONMENT)
        widget.environment.blockSignals(False)
        self.assertIsNone(widget.active_cica_gdb())
        rows = dict(widget.validation_confirmation_metadata({'dbname': 'sentencias'}, 'pg_temp', [], None))
        self.assertNotIn('Geodatabase CICA', rows)
        widget.environment.blockSignals(True)
        widget.environment.setCurrentText('Validaciones del modelo')
        widget.environment.blockSignals(False)
        self.assertIs(widget.active_cica_gdb(), prepared)
        rows = dict(widget.validation_confirmation_metadata({'dbname': 'sentencias'}, 'pg_temp', [], None))
        self.assertIn('Geodatabase CICA', rows)

    def test_missing_epsg_accepts_explicit_temporary_crs_without_changing_source(self):
        from qgis_control_calidad.cica_gdb import UnidentifiedGdbCrs
        before = {file.name: file.read_bytes() for file in self.source.iterdir() if file.is_file()}
        with patch('qgis_control_calidad.cica_gdb.spatial_srid', return_value=0):
            with self.assertRaises(UnidentifiedGdbCrs) as failure:
                prepare_gdb(self.source)
            self.assertEqual(failure.exception.layer_name, 'cica_terreno')
            self.assertTrue(failure.exception.wkt)
            prepared = prepare_gdb(self.source, crs_overrides={'cica_terreno': 4326})
        self.addCleanup(prepared.close)
        layer = prepared.layers['cica_terreno']
        self.assertEqual(layer.srid, 4326)
        with layer.csv_path.open() as stream:
            row = next(csv.reader(stream))
        self.assertTrue(row[layer.columns.index(layer.geometry_column)].startswith('SRID=4326;'))
        self.assertEqual(before, {file.name: file.read_bytes() for file in self.source.iterdir() if file.is_file()})

    def test_crs_equivalence_is_accepted_even_with_lower_match_confidence(self):
        from unittest.mock import MagicMock
        from qgis_control_calidad.cica_gdb import spatial_srid
        layer = MagicMock(); reference = layer.GetSpatialRef.return_value
        reference.Clone.return_value = reference
        reference.AutoIdentifyEPSG.side_effect = RuntimeError('No authority')
        reference.GetAuthorityName.return_value = None
        candidate = MagicMock()
        candidate.GetAuthorityName.return_value = 'EPSG'
        candidate.GetAuthorityCode.return_value = '9377'
        reference.FindMatches.return_value = [(candidate, 70)]
        reference.IsSame.return_value = True
        self.assertEqual(spatial_srid(layer), 9377)
        reference.IsSame.assert_called_once_with(candidate)

    def test_unidentified_crs_assigns_9377_without_dialog(self):
        from qgis_control_calidad.cica_gdb import UnidentifiedGdbCrs
        prepared = self.prepared()
        dialog = CicaIngestionDialog()
        with patch('qgis_control_calidad.ingestion.QFileDialog.getOpenFileName', return_value=('entrada.zip', '')), \
             patch('qgis_control_calidad.ingestion.prepare_gdb', side_effect=[UnidentifiedGdbCrs('U_CONSTRUCCION'), prepared]) as loader, \
             patch('qgis.gui.QgsProjectionSelectionDialog') as picker:
            dialog.choose_gdb()
        picker.assert_not_called()
        self.assertEqual(loader.call_count, 2)
        self.assertEqual(loader.call_args.kwargs['crs_overrides']['U_CONSTRUCCION'], 9377)
        self.assertIs(dialog.prepared_gdb, prepared)
        self.assertTrue(dialog.isEnabled())
        dialog.close()
