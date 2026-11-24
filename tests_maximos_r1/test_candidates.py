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
