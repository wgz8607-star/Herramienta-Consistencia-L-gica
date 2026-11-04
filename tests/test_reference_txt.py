import csv
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from qgis_control_calidad.reference_data import prepare_reference, REQUIRED


class TxtReferencesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def source(self, kind, changes=None):
        width = 312 if kind == 'R1' else 330
        line = [' '] * width
        def put(a, b, value):
            line[a-1:b] = list(value.ljust(b-a+1))
        put(1,30,'000010200000000000000000000001')
        put(31,31,kind[1]);put(32,34,'001');put(35,37,'001')
        if kind == 'R1':
            put(38,137,'NOMBRE Ñ');put(253,253,'A');put(254,268,'000000073047,22')
            put(269,274,'000123');put(275,289,'000000000001234');put(290,297,'01012026')
        else:
            put(38,55,'001-000123');put(84,98,'000000073047,22');put(127,141,'000000000001,50')
            put(184,189,'000123');put(232,237,'000045');put(280,285,'000000');put(308,315,'01012026')
        if changes:
            for a,b,value in changes:
                put(a,b,value)
        return ''.join(line)

    def prepare(self, kind, text, encoding='cp1252'):
        path = Path(self.temp.name) / (kind + '.TXT')
        path.write_bytes(text.encode(encoding))
        prepared = prepare_reference(kind, path)
        self.addCleanup(prepared.close)
        return prepared, path

    def test_fixed_width_fields_decimals_and_duplicate_records_are_preserved(self):
        for kind in ('R1','R2'):
            line = self.source(kind)
            prepared, source = self.prepare(kind,line+'\r\n'+line+'\r\n', 'cp1252' if kind=='R1' else 'utf-8-sig')
            self.assertEqual(prepared.row_count,1 if kind=='R1' else 2)
            self.assertTrue(REQUIRED[kind] <= set(prepared.columns))
            with prepared.csv_path.open(encoding='utf-8',newline='') as stream:
                rows=list(csv.reader(stream))
            if kind=='R2':
                self.assertEqual(rows[0], rows[1])
            else:
                self.assertEqual(prepared.duplicate_count,1)
            row=dict(zip(prepared.columns,rows[0]))
            self.assertEqual(row['numero_predial'],'000010200000000000000000000001')
            self.assertEqual(row['registro_original'],line)
            area=row['area_terreno' if kind=='R1' else 'area_terreno_1']
            self.assertEqual(Decimal(area),Decimal('73047.22'))
            self.assertEqual(row['vigencia'],'01012026')
            self.assertTrue(source.exists())
            if kind=='R2':
                self.assertEqual(row['matricula_inmobiliaria'],'001-000123')
                self.assertEqual(Decimal(row['area_construida_1']),123)

    def test_wrong_width_type_and_invalid_number_fail_with_line(self):
        for text in (self.source('R1')[:-1],self.source('R2')[:312],self.source('R1',[(254,268,'NO NUMERICO')])):
            with self.assertRaisesRegex(ValueError,'línea 1'):
                self.prepare('R1',text)

    def test_matricula_zeroes_are_text_and_never_coerced_to_excel_number(self):
        prepared, _ = self.prepare('R2',self.source('R2',[(38,55,'00000000000000000')]))
        with prepared.csv_path.open(encoding='utf-8',newline='') as stream:
            row=dict(zip(prepared.columns,next(csv.reader(stream))))
        self.assertEqual(row['matricula_inmobiliaria'],'00000000000000000')

    def test_empty_file_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'no contiene registros'):
            self.prepare('R2','\n')
