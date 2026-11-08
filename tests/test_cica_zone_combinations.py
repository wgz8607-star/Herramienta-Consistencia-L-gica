import csv
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import MagicMock,patch
from qgis_control_calidad.cica_progress import CicaProgressDialog
from qgis_control_calidad.territorial_statistics import read_cica_predio_details,cica_predio_details_from_snapshot
from test_temporary_references import app

ROWS=[('08421','Urbano','01','ASIGNADO',10,8,2,0),('08421','Centro poblado','02','TRAMITADO',7,6,1,0),('08421','Centro poblado','03','ASIGNADO',4,2,2,0),('08421','Rural','00','ASIGNADO',6,4,2,0)]


class CicaZoneCombinationTests(unittest.TestCase):
    def dialog(self):
        with patch('qgis_control_calidad.cica_progress.QTimer.singleShot'):
            dialog=CicaProgressDialog(lambda:{})
        self.addCleanup(dialog.close)
        dialog.set_data({'rows':ROWS,'snc_stages':('ASIGNADO',),'recognition_stages':('ASIGNADO',),'quality_stages':('ASIGNADO',)})
        return dialog

    def test_clicks_add_remove_and_clear_zones_then_restore_all(self):
        dialog=self.dialog()
        self.assertEqual(dialog.values['total'].text(),'27')
        dialog.zone_buttons['Urbano'].click()
        self.assertEqual(dialog.values['total'].text(),'10')
        dialog.zone_buttons['Rural'].click()
        self.assertEqual(dialog.values['total'].text(),'16')
        self.assertTrue(dialog.zone_buttons['Urbano'].isChecked())
        self.assertTrue(dialog.zone_buttons['Rural'].isChecked())
        dialog.zone_buttons['Urbano'].click()
        self.assertEqual(dialog.values['total'].text(),'6')
        dialog.zone_buttons['Rural'].click()
        self.assertEqual(dialog.values['total'].text(),'0')
        self.assertEqual(dialog.final_scope.text(),'Sin zonas seleccionadas')
        dialog.zone_buttons[''].click()
        self.assertEqual(dialog.values['total'].text(),'27')
        self.assertTrue(dialog.zone_buttons[''].isChecked())

    def test_cp_code_only_filters_cp_and_survives_combining_all_three_zones(self):
        dialog=self.dialog()
        dialog.zone_buttons['Centro poblado'].click();dialog.select_cp('02')
        self.assertEqual(dialog.values['total'].text(),'7')
        dialog.zone_buttons['Urbano'].click()
        self.assertEqual(dialog.values['total'].text(),'17')
        self.assertFalse(dialog.cp_container.isHidden())
        dialog.zone_buttons['Rural'].click()
        self.assertEqual(dialog.values['total'].text(),'23')
        self.assertEqual(dialog.values['active'].text(),'18')
        self.assertEqual(dialog.values['cancelled'].text(),'5')
        self.assertEqual(dialog.table.topLevelItemCount(),3)
        self.assertEqual(dialog.snc.text(),'16')
        dialog.zone_buttons['Centro poblado'].click()
        self.assertEqual(dialog.values['total'].text(),'16')
        self.assertTrue(dialog.cp_container.isHidden())
        dialog.zone_buttons[''].click()
        self.assertEqual(dialog.values['total'].text(),'27')

    def test_refresh_preserves_combination_and_does_not_mutate_data(self):
        dialog=self.dialog();dialog.toggle_zone('Urbano');dialog.toggle_zone('Rural')
        dialog.set_data({'rows':ROWS})
        self.assertEqual(dialog.values['total'].text(),'16')
        self.assertEqual(len(ROWS),4)

    def test_sql_and_snapshot_detail_use_same_zone_union_and_cp_scope(self):
        npns=['08421'+code+'0'*23 for code in ('01','00','02','03','XX')]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'data.csv'
            with path.open('w',newline='') as stream:
                csv.writer(stream).writerows((npn,'ASIGNADO','ACTIVO') for npn in npns)
            snapshot=SimpleNamespace(columns=('numero_predial','etapa','estado'),csv_path=path)
            for selection,cp,expected in [(('Urbano','Rural'),'',2),(('Urbano','Centro poblado'),'02',2),((),'',0),('','',5)]:
                local=cica_predio_details_from_snapshot(snapshot,selection,cp)
                self.assertEqual(len(local['rows']),expected)
                connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
                cursor.fetchall.return_value=[]
                with patch('psycopg2.connect',return_value=connection):
                    read_cica_predio_details({},'08421',selection,cp)
                query,args=cursor.execute.call_args.args
                query=query.replace('::text','').replace(' ~ ',' REGEXP ').replace('%s','?')
                db=sqlite3.connect(':memory:')
                try:
                    db.create_function('btrim',1,lambda value:value.strip() if value is not None else None)
                    db.create_function('regexp',2,lambda pattern,value:bool(__import__('re').search(pattern,value or '')))
                    db.execute("ATTACH DATABASE ':memory:' AS snc_cica_copy")
                    db.execute('CREATE TABLE snc_cica_copy.cica_predio (numero_predial TEXT,etapa TEXT,estado TEXT)')
                    db.executemany('INSERT INTO snc_cica_copy.cica_predio VALUES (?,?,?)',[(npn,'ASIGNADO','ACTIVO') for npn in npns])
                    self.assertEqual(db.execute(query,args).fetchall(),local['rows'])
                finally:db.close()
