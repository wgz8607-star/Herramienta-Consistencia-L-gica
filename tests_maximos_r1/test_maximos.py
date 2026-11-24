import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock,patch
from openpyxl import Workbook,load_workbook
from validador_renumeracion.core import build_maxima,visible_rows
from validador_renumeracion.readers import inspect_excel,file_records
from validador_renumeracion.exporter import export_maxima
from validador_renumeracion.database import list_tables,database_records


def npn(zone='01',sector='010000',block='0010',plot='0003',municipality='41020',condition='0'):
    return municipality+zone+sector+block+plot+condition+'00000000'


class MaximaTests(unittest.TestCase):
    def result(self):
        values=[npn(),npn(plot='0009'),npn(block='0012',plot='0002'),npn(sector='020000',block='0002',plot='0040'),npn(zone='02',block='0004'),npn(zone='03',block='0008'),npn(zone='00',block='0000',plot='0060'),npn(municipality='25377',block='0099'),npn(), ' '+npn()+' ',None,'',npn()[:-1],123]
        return build_maxima(enumerate(values,2))

    def test_maxima_are_separate_by_municipality_zone_prefix_and_full_block(self):
        result=self.result()
        self.assertEqual(result.unique_npns,8)
        self.assertEqual(result.duplicates,2)
        self.assertEqual(result.blanks,2)
        self.assertEqual(len(result.invalid),2)
        zones={(r['municipality'],r['zone']):r for r in result.zones}
        self.assertEqual(zones[('41020','01')]['max_m'],'0012')
        self.assertEqual(zones[('25377','01')]['max_m'],'0099')
        prefixes={r['prefix13']:r for r in result.prefixes}
        self.assertEqual(prefixes[npn()[:13]]['max_m'],'0012')
        self.assertEqual(prefixes[npn(sector='020000')[:13]]['max_m'],'0002')
        blocks={r['block17']:r for r in result.blocks}
        self.assertEqual(blocks[npn()[:17]]['max_t'],'0009')
        self.assertEqual(blocks[npn()[:17]]['next_t'],'0010')
        self.assertEqual(blocks[npn()[:17]]['witness'],npn(plot='0009'))
        self.assertEqual(zones[('41020','02')]['max_m'],'0004')
        self.assertEqual(zones[('41020','03')]['max_m'],'0008')

    def test_conditions_8_and_9_do_not_create_extra_terrain_codes(self):
        result=build_maxima(enumerate([npn(condition='0'),npn(condition='8'),npn(condition='9')]))
        self.assertEqual(result.unique_npns,3)
        self.assertEqual(result.blocks[0]['plots'],1)
        self.assertEqual(result.blocks[0]['max_t'],'0003')

    def test_exhaustion_zeroes_and_empty_reference_are_not_guessed(self):
        result=build_maxima([(2,npn(block='9999',plot='9999'))])
        self.assertEqual(result.prefixes[0]['next_m'],'AGOTADO (9999)')
        self.assertEqual(result.blocks[0]['next_t'],'AGOTADO (9999)')
        empty=build_maxima([(2,None),(3,'incorrecto')])
        self.assertEqual(empty.zones,[])
        self.assertEqual(empty.blocks,[])

    def test_filters_and_fingerprint_ignore_record_order(self):
        result=self.result();rows=visible_rows(result.blocks,'41020','01',npn()[:17])
        self.assertEqual(len(rows),1)
        first=build_maxima([(1,npn()),(2,npn(plot='0009'))])
        second=build_maxima([(1,npn(plot='0009')),(2,npn()),(3,npn())])
        self.assertEqual(first.fingerprint,second.fingerprint)

    def test_excel_reader_uses_r1_sheet_not_renumeration_result_and_reports_numeric_npns(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'r1.xlsx';book=Workbook();book.active.title='Resultado';book.active.append(['Nuevo','Provisional'])
            sheet=book.create_sheet('R1');sheet.append(['NUMERO_PREDIAL','Otro']);sheet.append([npn(),'x']);sheet.append([123,'x']);book.save(path);book.close()
            before=path.read_bytes();names,selected,header,headers,column=inspect_excel(path)
            self.assertEqual(selected,'R1')
            result=build_maxima(file_records(path,selected,header,column))
            self.assertEqual(result.unique_npns,1);self.assertEqual(len(result.invalid),1)
            self.assertEqual(path.read_bytes(),before)

    def test_excel_prefers_complete_numero_predial_over_short_nopredial(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'r1.xlsx';book=Workbook();book.active.append(['NoPredial','numero predial']);book.active.append([npn()[5:],npn()]);book.save(path);book.close()
            self.assertEqual(inspect_excel(path)[-1],1)

    def test_txt_reader_preserves_full_npn_and_rejects_wrong_record_type(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'r1.TXT';path.write_bytes((npn()+'1'+' '*(312-31)+'\r\n').encode('cp1252'))
            self.assertEqual(list(file_records(path)),[(1,npn())])
            path.write_text(npn()+'2'+' '*(312-31))
            with self.assertRaises(ValueError):list(file_records(path))

    def test_export_keeps_npns_as_text_filters_visible_rows_and_includes_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'maximos.xlsx';result=self.result()
            export_maxima(path,result,'R1 de prueba',{},'41020','02')
            book=load_workbook(path,data_only=True)
            self.assertEqual(book['Por zona'].max_row,2)
            self.assertEqual(book['Por manzana'].max_row,2)
            self.assertEqual(book['Por manzana'].cell(2,12).data_type,'s')
            self.assertEqual(book['Registros no utilizados'].max_row,3)
            self.assertIn('R1 de prueba',[row[1].value for row in book['Resumen']])
            book.close()

    def test_database_catalog_and_reader_are_readonly_and_quote_identifiers(self):
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value=[('r1_41020_20260930','NUMERO_PREDIAL'),('r2_41020_20260930','numero_predial'),('otra','nombre')]
        with patch('psycopg2.connect',return_value=connection):
            tables=list_tables({},'r1_r2',True)
        self.assertEqual(tables,[('r1_41020_20260930','NUMERO_PREDIAL')])
        connection.set_session.assert_called_once_with(readonly=True)
        connection.close.assert_called_once()
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.__iter__.return_value=iter([(npn(),)])
        with patch('psycopg2.connect',return_value=connection):
            rows=list(database_records({},'public','tabla con espacios','NUMERO_PREDIAL'))
        self.assertEqual(rows,[(1,npn())])
        self.assertTrue(connection.set_session.call_args.kwargs['readonly'])
        query=cursor.execute.call_args.args[0]
        from psycopg2 import sql
        def render(value):
            if isinstance(value,sql.SQL):return value.string
            if isinstance(value,sql.Identifier):return '.'.join('"'+x+'"' for x in value.strings)
            return ''.join(render(x) for x in value)
        self.assertEqual(render(query),'SELECT "NUMERO_PREDIAL"::text FROM "public"."tabla con espacios"')
        connection.close.assert_called_once()
