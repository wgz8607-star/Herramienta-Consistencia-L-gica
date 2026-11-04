import unittest
from openpyxl import Workbook
from qgis_control_calidad.report_exceptions import prepare_validation_index


class ReportGdbMetadataTests(unittest.TestCase):
    def test_summary_shows_original_gdb_name_or_explicit_absence(self):
        for value in ('GDB_20261009.gdb 2.zip','GDB_20261009.gdb','GDB no cargada'):
            sheet=Workbook().active
            prepare_validation_index(sheet,{'Modelo':'CICA','Geodatabase CICA':value},'Municipio',title='Resumen ejecutivo')
            rows=[row for row in sheet.iter_rows(values_only=True) if row[0]=='Geodatabase CICA']
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0][1],value)

    def test_other_reports_and_internal_model_do_not_add_gdb_row(self):
        for title,metadata in [('Detalle Validación',{'Geodatabase CICA':'prueba.gdb'}),('Resumen ejecutivo',{'Modelo':'Modelo Interno'})]:
            sheet=Workbook().active
            prepare_validation_index(sheet,metadata,'Municipio',title=title)
            self.assertNotIn('Geodatabase CICA',[row[0] for row in sheet.iter_rows(values_only=True)])
