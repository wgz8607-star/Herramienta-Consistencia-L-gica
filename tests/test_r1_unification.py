import csv
import hashlib
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from openpyxl import Workbook
from qgis_control_calidad.reference_data import PreparedReference, REQUIRED, prepare_reference, install_reference
from qgis_control_calidad.r1_unification import unify_r1
from qgis_control_calidad.public_references import prepare_public_references
from qgis_control_calidad.territorial_statistics import read_source_statistics
from test_cica_and_formats import CicaConnection
from test_temporary_references import render


class R1UnificationTests(unittest.TestCase):
    def raw(self,kind='R1'):
        directory=tempfile.TemporaryDirectory()
        reference=PreparedReference(kind,'origen',('numero_predial','area_terreno'),6,'original',Path(directory.name)/'original.csv',directory)
        with reference.csv_path.open('w',encoding='utf-8',newline='') as stream:
            csv.writer(stream).writerows([[' 000010100000000000000000000001 ','10'],['000010100000000000000000000001','99'],['000010100000000000000000000002','20'],['000010100000000000000000000002','20'],['','30'],['   ','40']])
        self.addCleanup(reference.close)
        return reference

    def rows(self,reference):
        with reference.csv_path.open(encoding='utf-8',newline='') as stream:return list(csv.reader(stream))

    def test_first_record_is_kept_without_summing_and_statistics_retain_source_counts(self):
        ref=self.raw();original=ref.csv_path;before=original.read_bytes()
        result=unify_r1(ref)
        self.assertEqual(self.rows(result),[['000010100000000000000000000001','10'],['000010100000000000000000000002','20']])
        self.assertEqual(result.row_count,2)
        self.assertEqual(result.original_row_count,6)
        self.assertEqual(result.duplicate_count,2)
        self.assertEqual(result.missing_npn_count,2)
        self.assertEqual(original.read_bytes(),before)
        self.assertIs(unify_r1(ref),ref)
        stats=read_source_statistics({},'','R1',ref)
        self.assertEqual((stats['total'],stats['row_count'],stats['duplicates'],stats['missing_npn']),(2,6,2,2))

    def test_installation_also_guards_old_raw_references_and_r2_is_unchanged(self):
        reference=self.raw();connection=CicaConnection()
        with patch('psycopg2.sql.Composed.as_string',lambda self,context:render(self)):
            install_reference(connection,reference)
        copied=next(event[2] for event in connection.events if event[0]=='copy')
        self.assertEqual(len(copied),2)
        self.assertEqual(copied[0][1],'10')
        r2=self.raw('R2');path=r2.csv_path
        self.assertIs(unify_r1(r2),r2)
        self.assertEqual(r2.csv_path,path)
        self.assertEqual(len(self.rows(r2)),6)

    def test_excel_file_and_first_values_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'r1.xlsx';book=Workbook();sheet=book.active
            columns=sorted(REQUIRED['R1']);sheet.append(columns)
            for area in ('10','99'):
                sheet.append(['000010100000000000000000000001' if col=='numero_predial' else area if col=='area_terreno' else '1' for col in columns])
            book.save(path);book.close();before=path.read_bytes()
            reference=prepare_reference('R1',path)
            try:
                self.assertEqual(reference.row_count,1)
                self.assertEqual(self.rows(reference)[0][columns.index('area_terreno')],'10')
                self.assertEqual(reference.duplicate_count,1)
                self.assertEqual(path.read_bytes(),before)
            finally:reference.close()

    def test_public_snapshot_unifies_by_npn_before_any_rule_executes(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.description=[SimpleNamespace(name='numero_predial'),SimpleNamespace(name='areaterreno')]
        cursor.fetchmany.side_effect=[[('00001','10'),('00001','99')],[]]
        with patch('qgis_control_calidad.public_references.read_public_catalog',return_value={'R1':['r1_local'],'R2':[]}),patch('psycopg2.connect',return_value=connection):
            references=prepare_public_references({}, {'R1':'r1_local'})
        try:
            self.assertEqual(references['R1'].row_count,1)
            self.assertEqual(self.rows(references['R1']),[['00001','10']])
        finally:references['R1'].close()

    def test_current_reference_snapshot_applies_same_policy(self):
        from qgis_control_calidad.current_references import prepare_current_references
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        columns=sorted(REQUIRED['R1']);cursor.description=[SimpleNamespace(name=name) for name in columns]
        cursor.fetchmany.side_effect=[[
            tuple('00001' if name=='numero_predial' else area if name=='area_terreno' else '1' for name in columns) for area in ('10','99')],[]]
        selection={'divipola':'08421','stamp':'20260930','tables':{'R1':'r1_08421_20260930'}}
        with patch('psycopg2.connect',return_value=connection):
            references=prepare_current_references({},selection,{'R1'})
        try:
            self.assertEqual(references['R1'].row_count,1)
            self.assertEqual(self.rows(references['R1'])[0][columns.index('area_terreno')],'10')
            self.assertEqual(references['R1'].duplicate_count,1)
        finally:references['R1'].close()
