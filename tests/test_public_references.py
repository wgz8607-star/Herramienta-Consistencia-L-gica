import csv
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from qgis_control_calidad.public_references import read_public_catalog, prepare_public_references, connection_identity
from qgis_control_calidad.reference_data import REQUIRED
from qgis_control_calidad.dialog import ControlCalidadDialog
from test_cica_and_formats import app


class PublicReferencesTests(unittest.TestCase):
    def test_catalog_detects_tables_by_columns_and_uses_readonly_connection(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value=[('mi_r1',name.upper()) for name in sorted(REQUIRED['R1'])]+[('mi_r2',name) for name in sorted(REQUIRED['R2'])]+[('incompleta','numero_predial')]
        with patch('psycopg2.connect',return_value=connection):
            catalog=read_public_catalog({'dbname':'catastro'})
        self.assertEqual(catalog,{'R1':['mi_r1'],'R2':['mi_r2']})
        connection.set_session.assert_called_once_with(readonly=True)
        self.assertIn("c.table_schema='public'",cursor.execute.call_args.args[0])
        connection.close.assert_called_once()

    def test_catalog_also_recognizes_minimal_r1_with_areaterreno(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value=[('r1_minimo','numero_predial'),('r1_minimo','areaterreno'),('r1_incompleto','numero_predial')]
        with patch('psycopg2.connect',return_value=connection):
            self.assertEqual(read_public_catalog({}), {'R1':['r1_minimo'],'R2':[]})

    def test_minimal_public_r1_maps_area_alias_only_in_temporary_snapshot(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.description=[SimpleNamespace(name='numero_predial'), SimpleNamespace(name='areaterreno')]
        cursor.fetchmany.side_effect=[[('000010000000000000000000000001','123.45')],[]]
        with patch('qgis_control_calidad.public_references.read_public_catalog',return_value={'R1':['r1_minimo'],'R2':[]}),patch('psycopg2.connect',return_value=connection):
            refs=prepare_public_references({}, {'R1':'r1_minimo'})
        try:
            self.assertEqual(refs['R1'].columns,('numero_predial','area_terreno'))
            with refs['R1'].csv_path.open(encoding='utf-8',newline='') as stream:
                self.assertEqual(next(csv.reader(stream)),['000010000000000000000000000001','123.45'])
            self.assertEqual(refs['R1'].row_count,1)
        finally:
            refs['R1'].close()

    def test_option_labels_and_precargados_date_follow_selected_municipality(self):
        dialog=ControlCalidadDialog()
        try:
            self.assertEqual(dialog.reference_mode.itemText(0),'Opción 1: Archivos r1 y r2 cargados por usuario')
            self.assertEqual(dialog.reference_mode.itemText(2),'Opción 3: Archivos r1 y r2 cargados en "Public" de la base seleccionada')
            dialog.municipality.addItem('Puerto Wilches',{'date':'2026-09-30','tables':{'R1':'r1_68575_20260930'}})
            dialog.show_current_reference()
            self.assertTrue(dialog.reference_mode.itemText(1).endswith('30/09/2026'))
            dialog.municipality.clear()
            self.assertTrue(dialog.reference_mode.itemText(1).endswith('Sin fecha seleccionada'))
        finally:
            dialog.close()

    def test_public_snapshot_keeps_data_and_never_writes_source(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        columns=sorted(REQUIRED['R1']);cursor.description=[SimpleNamespace(name=n) for n in columns]
        values=['000010200000000000000000000001' if n=='numero_predial' else '1' for n in columns]
        cursor.fetchmany.side_effect=[[tuple(values)],[]]
        with patch('qgis_control_calidad.public_references.read_public_catalog',return_value={'R1':['r1_local'],'R2':[]}),patch('psycopg2.connect',return_value=connection):
            refs=prepare_public_references({'dbname':'catastro'},{'R1':'r1_local'})
        try:
            self.assertEqual(refs['R1'].filename,'public.r1_local')
            self.assertEqual(refs['R1'].row_count,1)
            with refs['R1'].csv_path.open(encoding='utf-8',newline='') as stream:
                self.assertEqual(next(csv.reader(stream)),values)
            self.assertTrue(connection.set_session.call_args.kwargs['readonly'])
            from test_temporary_references import render
            queries=[render(call.args[0]) for call in cursor.execute.call_args_list]
            self.assertIn('SELECT * FROM "public"."r1_local"',queries)
            self.assertFalse(any('CREATE' in q or 'INSERT' in q or 'UPDATE' in q for q in queries))
        finally:
            for ref in refs.values():ref.close()

    def test_third_option_is_independent_and_connection_change_invalidates_it(self):
        dialog=ControlCalidadDialog()
        params={'dbname':'catastro','user':'usuario'}
        reference=MagicMock();reference.csv_path.is_file.return_value=True
        dialog.public_references={'R1':reference}
        dialog.public_reference_identity=connection_identity(params)
        with patch.object(dialog,'connection_params',return_value=params):
            dialog.reference_mode.setCurrentIndex(2)
            self.assertEqual(dialog.reference_pages.currentIndex(),2)
            self.assertIs(dialog.active_local_references()['R1'],reference)
            self.assertEqual(dialog.missing_references([('A','regla','SELECT * FROM {esquema_r1}.{tabla_r1}','')]),[])
            dialog.public_connection_changed()
        reference.close.assert_called_once()
        self.assertEqual(dialog.public_references,{})
        dialog.close()
