import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from qgis_control_calidad.territorial_statistics import read_cica_stages, cica_stages_from_snapshot
from qgis_control_calidad.cica_data import prepare_csv


class CicaIndicatorsTests(unittest.TestCase):
    def source_rows(self):
        entries = [
            ('ASIGNADO', 'ACTIVO', 0, None), ('PARA_DISPOSITIVO', 'ACTIVO', 1, None),
            ('EN_DISPOSITIVO', 'ACTIVO', -1, None), ('SIN_ASIGNAR', 'ACTIVO', None, None),
            ('PRE_ASIGNADO', 'ACTIVO', 3, None), ('TRAMITADO', 'ACTIVO', 10, None),
            ('CONTROL_CALIDAD_GENERAL', 'ACTIVO', 5, None), ('CONTROL_CALIDAD_GRUPO', 'CANCELADO', 100, None),
            ('DEVUELTO', 'ACTIVO', 0, None), ('RECHAZADO', 'CANCELADO', 20, None),
            ('VALIDADO', 'ACTIVO', 7, 'DESCARGADO_AL_SNC'), ('VALIDADO', 'ACTIVO', 0, 'OTRO'),
            ('VALIDADO', 'CANCELADO', 3, 'DESCARGADO_AL_SNC'),
            ('ETAPA_NUEVA', 'ACTIVO', 1, None)]
        return [('084210200' + str(index).zfill(4), stage, state, area, control) for index, (stage, state, area, control) in enumerate(entries)]

    def test_exact_user_criteria_in_sql_match_snapshot_indicators(self):
        rows = self.source_rows()
        connection = MagicMock(); cursor = connection.cursor.return_value.__enter__.return_value
        fields = [('numero_predial', 'text'), ('etapa', 'text'), ('estado', 'text'), ('area_geo_num', 'numeric'), ('estado_control', 'text')]
        cursor.fetchall.side_effect = [fields, []]
        with patch('psycopg2.connect', return_value=connection): read_cica_stages({}, '08421', include_source=True)
        query, args = cursor.execute.call_args.args
        query = query.replace('::text', '').replace('::numeric', '').replace(' ~ ', ' REGEXP ').replace('%s', '?')
        db = sqlite3.connect(':memory:'); self.addCleanup(db.close)
        db.create_function('btrim', 1, lambda value: value.strip() if value else value)
        db.create_function('regexp', 2, lambda pattern, value: bool(__import__('re').search(pattern, value or '')))
        db.execute("ATTACH DATABASE ':memory:' AS snc_cica_copy")
        db.execute('CREATE TABLE snc_cica_copy.cica_predio (numero_predial TEXT, etapa TEXT, estado TEXT, area_geo_num NUMERIC, estado_control TEXT)')
        db.executemany('INSERT INTO snc_cica_copy.cica_predio VALUES (?,?,?,?,?)', rows)
        grouped = db.execute(query, args).fetchall()
        sql_totals = [sum(row[index] for row in grouped) for index in range(8, 16)]
        # recognized active/cancelled, quality active/cancelled, areas,
        # loaded SNC (including cancelled, per the supplied predicate), totals.
        self.assertEqual(sql_totals, [6, 3, 4, 3, 6, 2, 9, 7])
        with tempfile.TemporaryDirectory() as directory:
            import csv
            path = Path(directory) / 'predio.csv'
            with path.open('w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['numero_predial', 'etapa', 'estado', 'area_geo_num', 'estado_control']); writer.writerows(rows)
            snapshot = prepare_csv('cica_predio', path)
            try:
                data = cica_stages_from_snapshot(snapshot)
                self.assertTrue(data['areas_available']); self.assertTrue(data['snc_available'])
                metric = data['indicator_rows'][0]
                names = ['recognized_active', 'recognized_cancelled', 'quality_active', 'quality_cancelled', 'with_areas', 'snc', 'recognized_total', 'quality_total']
                self.assertEqual([metric[name] for name in names], sql_totals)
                self.assertEqual(metric['codigo_zona'], '02')
                from test_temporary_references import app
                from qgis_control_calidad.cica_progress import CicaProgressDialog
                with patch('qgis_control_calidad.cica_progress.QTimer.singleShot'):
                    dialog = CicaProgressDialog(lambda: {})
                try:
                    dialog.set_data(data); dialog.set_zone('Centro poblado'); dialog.select_cp('02')
                    self.assertIn('6 | 54.5 %', dialog.metric_widgets['recognition'][0][1].text())
                    self.assertIn('4 | 36.4 %', dialog.metric_widgets['quality'][0][1].text())
                    self.assertEqual(dialog.no_areas.text(), '5')
                    self.assertEqual(dialog.snc.text(), '2')
                finally:
                    dialog.close()
            finally: snapshot.close()

    def test_area_geografica_text_fallback_and_missing_control_are_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'predio.csv'
            path.write_text('numero_predial;estado;etapa;area_geografica\n084210100001;ACTIVO;VALIDADO;1,5\n084210100002;CANCELADO;VALIDADO;100\n084210100003;ACTIVO;ASIGNADO;texto\n')
            snapshot = prepare_csv('cica_predio', path)
            try:
                data = cica_stages_from_snapshot(snapshot)
                self.assertTrue(data['areas_available']); self.assertFalse(data['snc_available'])
                self.assertEqual(data['indicator_rows'][0]['with_areas'], 1)
                self.assertIsNone(data['indicator_rows'][0]['snc'])
            finally: snapshot.close()
