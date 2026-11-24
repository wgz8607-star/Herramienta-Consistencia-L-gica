import unittest
from validador_renumeracion.candidates import identify_candidates
from test_maximos import npn


class CandidateTests(unittest.TestCase):
    def code(self,m='0001',t='0001',condition='0'):
        value=npn();return value[:13]+m+t+condition+value[22:]

    def test_cica_checks_both_positions_and_deduplicates(self):
        records=[self.code(m='9001'),self.code(t='8002'),self.code(m='7001',t='9001'),self.code(),self.code(m='9001')]
        result=identify_candidates(enumerate(records,1),'CICA')
        self.assertEqual(len(result['rows']),3);self.assertEqual(result['duplicates'],1)
        self.assertEqual({r[7] for r in result['rows']},{'Manzana','Terreno','Manzana y terreno'})

    def test_model_any_letter_special_condition_and_invalids(self):
        result=identify_candidates(enumerate([self.code(m='Z001'),self.code(t='c001',condition='9'),self.code(m='9001'),'123',None],1),'Modelo Interno')
        self.assertEqual(len(result['rows']),2);self.assertEqual(len(result['invalid']),2)
        self.assertTrue(any('revisión especial pendiente' in row[-1] for row in result['rows']))
        self.assertEqual(len(identify_candidates([(1,self.code(m='A001'))],'CICA')['invalid']),1)

    def test_source_dialog_resets_and_uses_explicit_connection_source(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from unittest.mock import patch
        parent=MaximaDialog();dialog=CandidateDialog(parent);dialog._cica_password='test'
        try:
            self.assertEqual(dialog.schema.currentText(),'snc_cica_copy')
            with patch.object(parent,'params',return_value={}) as params:
                self.assertEqual(dialog.params()['dbname'],'sentencias')
                dialog.model.setCurrentIndex(1);dialog.params();self.assertFalse(params.call_args.kwargs['preloaded'])
            self.assertEqual(dialog.schema.count(),0)
            self.assertIsNone(dialog.result)
        finally:dialog.close();parent.close()

    def test_source_read_is_readonly_and_filters_municipality(self):
        from unittest.mock import MagicMock,patch
        from validador_renumeracion.database import source_records
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value=('sentencias','172.19.3.225',5432,'admin_ant','admin_ant',True,True)
        cursor.fetchall.return_value=[('ILC_Predio','numero_predial_nacional')]
        cursor.__iter__.return_value=iter([(self.code(m='A001'),)])
        with patch('psycopg2.connect',return_value=connection):
            rows=list(source_records({'dbname':'modelo'},'Modelo Interno','esquema','41020'))
        self.assertEqual(len(rows),1)
        self.assertEqual(cursor.execute.call_args.args[1],('41020',))
        self.assertTrue(connection.set_session.call_args.kwargs['readonly'])
        connection.close.assert_called_once()
        with self.assertRaises(ValueError):list(source_records({'dbname':'otra'},'CICA','snc_cica_copy'))

    def test_direct_postgres_source_parameters(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        parent=MaximaDialog();dialog=CandidateDialog(parent);dialog._cica_password='test'
        try:
            dialog.connection_mode.setCurrentIndex(1)
            for key,value in {'host':'localhost','dbname':'catastro','user':'reader'}.items():dialog.direct[key].setText(value)
            self.assertEqual(dialog.params()['dbname'],'sentencias')
            dialog.model.setCurrentIndex(1)
            self.assertEqual(dialog.model.currentText(),'Modelo Interno de Levantamiento 1.0')
            self.assertEqual(dialog.params()['dbname'],'catastro')
        finally:dialog.close();parent.close()

    def test_cica_requires_validado_and_descargado_with_optional_municipality(self):
        from unittest.mock import MagicMock,patch
        from psycopg2 import sql
        from validador_renumeracion.database import source_records
        def render(value):
            if isinstance(value,sql.SQL):return value.string
            if isinstance(value,sql.Identifier):return '.'.join('"'+part+'"' for part in value.strings)
            return ''.join(render(part) for part in value)
        for municipality in ('','41020'):
            connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
            cursor.fetchone.return_value=('sentencias','172.19.3.225',5432,'admin_ant','admin_ant',True,True)
            cursor.fetchall.return_value=[('cica_predio','numero_predial')]
            cursor.__iter__.return_value=iter([])
            with patch('psycopg2.connect',return_value=connection):
                list(source_records({'dbname':'sentencias'},'CICA','snc_cica_copy',municipality))
            query,args=cursor.execute.call_args.args
            self.assertIn('"etapa"=%s AND "estado_control"=%s',render(query))
            self.assertEqual(args,('VALIDADO','DESCARGADO_AL_SNC')+((municipality,) if municipality else ()))
            self.assertEqual('left(trim(' in render(query),bool(municipality))

    def test_cica_zones_are_combined_and_empty_selection_is_rejected(self):
        from unittest.mock import MagicMock,patch
        from validador_renumeracion.database import source_records
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value=('sentencias','172.19.3.225',5432,'admin_ant','admin_ant',True,True)
        cursor.fetchall.return_value=[('cica_predio','numero_predial')]
        cursor.__iter__.return_value=iter([])
        with patch('psycopg2.connect',return_value=connection):
            list(source_records({'dbname':'sentencias'},'CICA','snc_cica_copy','41020',('URBANO','CP')))
        self.assertEqual(cursor.execute.call_args.args[1],('VALIDADO','DESCARGADO_AL_SNC','^01$','^(0[2-9]|[1-9][0-9])$','41020'))
        with self.assertRaises(ValueError):list(source_records({'dbname':'sentencias'},'CICA','snc_cica_copy',zones=()))

    def test_cica_hides_connections_and_filters_municipalities_by_department(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from unittest.mock import patch
        parent=MaximaDialog();dialog=CandidateDialog(parent)
        try:
            self.assertTrue(dialog.connection_mode.isHidden())
            self.assertTrue(dialog.connection.isHidden())
            self.assertFalse(dialog.department.isHidden())
            parent.catalog={'41020':('Huila','Algeciras'),'25377':('Cundinamarca','La Calera')}
            with patch.object(dialog,'params',return_value={'dbname':'sentencias'}),patch('validador_renumeracion.candidate_dialog.cica_municipalities',return_value=['41020','25377']):dialog.load_cica_municipalities()
            dialog.department.setCurrentIndex(dialog.department.findData('Huila'))
            self.assertEqual(dialog.cica_municipality.count(),2)
            self.assertEqual(dialog.cica_municipality.itemData(1),'41020')
            dialog.model.setCurrentIndex(1)
            self.assertFalse(dialog.connection_mode.isHidden())
            self.assertTrue(dialog.department.isHidden())
        finally:dialog.close();parent.close()

    def test_cica_reuses_installed_validator_without_password_prompt(self):
        from validador_renumeracion.repository import repository_params
        params=repository_params()
        self.assertEqual(params['dbname'],'sentencias')
        self.assertTrue(params.get('password'))
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from unittest.mock import patch
        parent=MaximaDialog();dialog=CandidateDialog(parent)
        try:
            with patch.object(parent,'params',side_effect=AssertionError('No debe pedir conexión QGIS')):
                self.assertEqual(dialog.params(),params)
        finally:dialog.close();parent.close()

    def test_permission_diagnostic_reports_effective_user_without_credentials(self):
        from unittest.mock import MagicMock
        from validador_renumeracion.database import cica_access
        cursor=MagicMock()
        cursor.fetchone.return_value=('sentencias','172.19.3.225',5432,'conexion_otra','lector',False,True)
        with self.assertRaises(ValueError) as error:cica_access(cursor)
        self.assertIn('Usuario efectivo: lector',str(error.exception))
        self.assertIn('USAGE snc_cica_copy: False',str(error.exception))
        self.assertNotIn('password',str(error.exception))
        cursor.fetchone.return_value=('sentencias','172.19.3.225',5432,'admin_ant','admin_ant',True,True)
        self.assertIn('SELECT cica_predio: True',cica_access(cursor))

    def test_cica_hides_model_controls_and_omits_zone_selection(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        parent=MaximaDialog();dialog=CandidateDialog(parent)
        try:
            self.assertTrue(dialog.list_button.isHidden())
            self.assertTrue(dialog.schema.isHidden())
            self.assertTrue(dialog.copy_label.isHidden())
            self.assertNotIn('Modelo Interno',dialog.note.text())
            self.assertFalse(hasattr(dialog,'zones_widget'))
        finally:dialog.close();parent.close()

    def test_cica_dashboard_counts_and_state_denominators(self):
        from test_ui import app
        from validador_renumeracion.cica_progress import CicaProgressDialog
        from qgis.PyQt.QtCore import QTimer
        data={'rows':[('41020','Urbano','01','VALIDADO',10,8,2,0)],'indicator_rows':[{'divipola':'41020','zona':'Urbano','codigo_zona':'01','recognized_active':8,'recognized_cancelled':1,'quality_active':8,'quality_cancelled':1,'with_areas':7,'snc':9}],'areas_available':True,'snc_available':True}
        dialog=CicaProgressDialog(lambda:data)
        try:
            app.processEvents();dialog.set_data(data)
            self.assertEqual(dialog.values['total'].text(),'10')
            self.assertEqual(dialog.snc.text(),'9')
            self.assertIn('Faltan 1',dialog.remaining_widgets[('quality','cancelled')].text())
            self.assertTrue(dialog.zone_buttons['Rural'].isHidden())
        finally:dialog.close()

    def test_first_window_reads_latest_r1_and_enables_adjacent_maxima_button(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from unittest.mock import patch
        parent=MaximaDialog();dialog=CandidateDialog(parent)
        try:
            self.assertFalse(dialog.r1_button.isEnabled())
            dialog.cica_municipality.blockSignals(True)
            dialog.cica_municipality.addItem('Seleccione',None);dialog.cica_municipality.addItem('Algeciras','41020');dialog.cica_municipality.setCurrentIndex(1)
            dialog.cica_municipality.blockSignals(False);dialog.update_r1_availability()
            self.assertTrue(dialog.r1_button.isEnabled())
            rows=[('r1_41020_20260930','numero_predial'),('r1_41020_20261031','numero_predial'),('r1_25377_20261101','numero_predial')]
            with patch('validador_renumeracion.repository.repository_params',return_value={'dbname':'sentencias'}),patch('validador_renumeracion.database.list_tables',return_value=rows),patch('validador_renumeracion.database.database_records',return_value=iter([(1,self.code())])) as reader:
                dialog.read_selected_r1()
            self.assertEqual(reader.call_args.args[2],'r1_41020_20261031')
            self.assertIn('31/10/2026',dialog.r1_status.text())
            self.assertTrue(dialog.maxima_button.isEnabled())
            dialog.open_r1();self.assertTrue(parent.inputs.isHidden())
            dialog.cica_municipality.setCurrentIndex(0)
            self.assertFalse(dialog.maxima_button.isEnabled());self.assertIsNone(parent.result)
        finally:dialog.close();parent.close()

    def test_statistics_expand_from_prefix_9_to_prefix_17_and_count_unique_npns(self):
        from validador_renumeracion.candidates import candidate_statistics
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        first=self.code(m='9001',t='9001')
        paired=first[:21]+'2'+first[22:]
        other=self.code(m='9002',t='9003')
        other_sector=other[:7]+'02'+other[9:]
        result=identify_candidates(enumerate([first,paired,other,other_sector,first],1),'CICA')
        groups=candidate_statistics(result['rows'])
        self.assertEqual(len(groups),2)
        self.assertEqual(groups[0]['predios'],3)
        self.assertEqual(groups[0]['blocks'],2)
        self.assertEqual(groups[0]['plots'],2)
        self.assertEqual(sum(x['predios'] for x in groups[0]['children']),3)
        parent=MaximaDialog();dialog=CandidateDialog(parent)
        try:
            dialog.result=result;dialog.render_candidate_statistics()
            self.assertEqual(dialog.tree.topLevelItemCount(),2)
            item=dialog.tree.topLevelItem(0)
            self.assertEqual(len(item.text(0)),9)
            self.assertEqual(item.childCount(),2)
            self.assertEqual(len(item.child(0).text(0)),17)
            self.assertEqual(item.child(0).childCount(),0)
        finally:dialog.close();parent.close()

    def test_two_sections_only_position14_creates_new_block_and_labels_match_zone(self):
        from validador_renumeracion.candidates import new_block_statistics,block_name
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        urban=self.code(m='9001')
        rural=urban[:5]+'00'+urban[7:]
        cp=urban[:5]+'02'+urban[7:]
        terrain_only=self.code(m='0001',t='9001')
        result=identify_candidates(enumerate([urban,rural,cp,terrain_only],1),'CICA')
        blocks=new_block_statistics(result['rows'])
        self.assertEqual(len(blocks),3)
        self.assertEqual([block_name(b['prefix']) for b in blocks],['Vereda','Manzana','Manzana'])
        parent=MaximaDialog();dialog=CandidateDialog(parent)
        try:
            dialog.result=result;dialog.render_candidate_statistics()
            self.assertEqual(dialog.new_blocks.topLevelItemCount(),3)
            self.assertIn('Vereda',dialog.new_blocks.topLevelItem(0).child(0).text(1))
            self.assertEqual(sum(int(dialog.tree.topLevelItem(i).text(2)) for i in range(dialog.tree.topLevelItemCount())),4)
        finally:dialog.close();parent.close()

    def test_new_blocks_group_by_prefix9_and_can_expand_and_collapse(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from qgis.PyQt.QtCore import Qt
        parent=MaximaDialog();dialog=CandidateDialog(parent)
        try:
            result=identify_candidates(enumerate([self.code(m='9001'),self.code(m='9002'),self.code(m='0001',t='9001')],1),'CICA')
            dialog.result=result;dialog.render_candidate_statistics()
            self.assertTrue(dialog.windowFlags() & Qt.WindowMinimizeButtonHint)
            self.assertTrue(dialog.windowFlags() & Qt.WindowMaximizeButtonHint)
            self.assertEqual(dialog.new_blocks.topLevelItemCount(),1)
            item=dialog.new_blocks.topLevelItem(0)
            self.assertEqual(len(item.text(0)),9)
            self.assertEqual(item.text(3),'2')
            self.assertEqual(item.childCount(),2)
            dialog.expand_blocks.click();self.assertTrue(item.isExpanded())
            dialog.collapse_blocks.click();self.assertFalse(item.isExpanded())
        finally:dialog.close();parent.close()

    def test_copy_date_appears_after_lookup_and_uses_latest_progress_start(self):
        from datetime import datetime
        from unittest.mock import patch
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        parent=MaximaDialog();dialog=CandidateDialog(parent)
        try:
            self.assertTrue(dialog.copy_label.isHidden())
            with patch.object(dialog,'params',return_value={}),patch('validador_renumeracion.candidate_dialog.cica_municipalities',return_value=['41020']),patch('validador_renumeracion.candidate_dialog.cica_copy_date',return_value=datetime(2026,11,24,13,29,50)):
                dialog.load_cica_municipalities()
            self.assertFalse(dialog.copy_label.isHidden())
            self.assertIn('Copia base CICA',dialog.copy_label.text())
            self.assertIn('24/11/2026 13:29:50',dialog.copy_label.text())
            self.assertGreater(dialog.connection_form.getWidgetPosition(dialog.copy_label)[0],dialog.connection_form.getWidgetPosition(dialog.cica_lookup)[0])
            dialog.model.setCurrentIndex(1)
            self.assertTrue(dialog.copy_label.isHidden())
        finally:dialog.close();parent.close()
