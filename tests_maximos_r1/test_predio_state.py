import unittest,tempfile
from pathlib import Path
from unittest.mock import MagicMock,patch
from openpyxl import load_workbook
from test_maximos import npn
from test_renumbering import old
from validador_renumeracion.candidates import identify_candidates
from validador_renumeracion.core import build_maxima
from validador_renumeracion.renumbering import generate_proposal,compare_proposal


def projected(states=('ACTIVO','ACTIVO','CANCELADO'),model='CICA'):
    block='0010' if model=='CICA' else '0010'
    plot='9001' if model=='CICA' else 'A001'
    records=[(i,old(block,plot,condition),state) for i,(condition,state) in enumerate(zip(('0','2','5'),states),1)]
    candidates=identify_candidates(records,model)
    r1=build_maxima([(1,npn(block='0010',plot='0020'))])
    return generate_proposal(candidates['rows'],r1,model),candidates,r1


def sql_text(value):
    from psycopg2 import sql
    if isinstance(value,sql.SQL):return value.string
    if isinstance(value,sql.Identifier):return '.'.join('"'+part+'"' for part in value.strings)
    return ''.join(sql_text(part) for part in value)


class PredioStateTests(unittest.TestCase):
    def test_third_condition5_cancelled_shares_one_terrain_preserves_condition(self):
        for model in ('CICA','Modelo Interno'):
            proposal,_,_=projected(model=model)
            self.assertEqual(len(proposal),3)
            self.assertTrue(all(row['status']=='Generado' for row in proposal))
            self.assertEqual({row['new'][17:21] for row in proposal},{'0021'})
            self.assertEqual({row['new'][21] for row in proposal},{'0','2','5'})
            self.assertEqual([row['predio_state'] for row in proposal],['ACTIVO','ACTIVO','CANCELADO'])
            comparison=compare_proposal(proposal,[{'line':i,'old':row['old'],'new':row['new']} for i,row in enumerate(proposal)],True)
            self.assertTrue(all(row['status']=='Coincide' for row in comparison))
            self.assertEqual([row['predio_state'] for row in comparison],['ACTIVO','ACTIVO','CANCELADO'])

    def test_active_or_unknown_condition5_is_not_approved(self):
        for state in ('ACTIVO',None,'','ESTADO INCONSISTENTE'):
            proposal,_,_=projected(states=('ACTIVO','ACTIVO',state))
            self.assertTrue(all(row['status']=='Pendiente' for row in proposal))
            self.assertTrue(all(not row['new'] for row in proposal))
        proposal,_,_=projected(states=('activo','ACTIVO',' cancelado '))
        self.assertTrue(all(row['status']=='Generado' for row in proposal))

    def test_additional_condition5_is_not_unrestricted_repetition(self):
        proposal,candidates,r1=projected()
        two=[row for row in candidates['rows'] if row[8]!='2']
        self.assertTrue(all(row['status']=='Pendiente' for row in generate_proposal(two,r1,'CICA')))
        extra=old('0010','9001','5',suffix='00000001')
        records=[(i,row[0],row[10]) for i,row in enumerate(candidates['rows'])]+[(5,extra,'CANCELADO')]
        rows=identify_candidates(records,'CICA')['rows']
        self.assertTrue(all(row['status']=='Pendiente' for row in generate_proposal(rows,r1,'CICA')))

    def test_duplicate_npn_with_conflicting_states_is_reported(self):
        number=old('0010','9001','5')
        candidates=identify_candidates([(1,number,'ACTIVO'),(2,number,'CANCELADO')],'CICA')
        self.assertEqual(candidates['duplicates'],1)
        self.assertEqual(candidates['rows'][0][10],'ESTADO INCONSISTENTE')
        r1=build_maxima([(1,npn())])
        self.assertEqual(generate_proposal(candidates['rows'],r1,'CICA')[0]['status'],'Pendiente')

    def test_cica_reader_uses_actual_estado_column(self):
        from validador_renumeracion.database import source_records
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value=('sentencias','172.19.3.225',5432,'admin_ant','admin_ant',True,True)
        cursor.fetchall.return_value=[('cica_predio','numero_predial'),('cica_predio','estado')]
        number=old('0010','9001','5');cursor.__iter__.return_value=iter([(number,'CANCELADO')])
        with patch('psycopg2.connect',return_value=connection):records=list(source_records({'dbname':'sentencias'},'CICA','snc_cica_copy'))
        self.assertEqual(records,[(1,number,'CANCELADO')])
        query,args=cursor.execute.call_args.args
        self.assertIn('"p"."estado"::text',sql_text(query))
        self.assertEqual(args,('VALIDADO','DESCARGADO_AL_SNC'))
        connection.set_session.assert_called_once_with(readonly=True,isolation_level='REPEATABLE READ')

    def test_model_uses_cancellation_novelty_containing_word_even_if_estado_exists(self):
        from validador_renumeracion.database import source_records
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        d='ilc_datosadicionaleslevantamientocatastral';n='ilc_estructuranovedadnumeropredial';t='ilc_estructuranovedadnumeropredial_tipo_novedad'
        cursor.fetchall.side_effect=[ [('ILC_Predio','numero_predial'),('ILC_Predio','t_id'),('ILC_Predio','estado')],
            [(d,'t_id'),(d,'ilc_predio'),(n,'ilc_dtsdcnltmntctstral_novedad_numeros_prediales'),(n,'tipo_novedad'),(t,'t_id'),(t,'ilicode')]]
        number=old('0010','A001','5');cursor.__iter__.return_value=iter([(number,'CANCELADO')])
        with patch('psycopg2.connect',return_value=connection):records=list(source_records({'dbname':'modelo'},'Modelo Interno','o_41020','41020'))
        query,args=cursor.execute.call_args.args;text=sql_text(query)
        self.assertEqual(args,('%cancelacion%','41020'))
        self.assertIn("THEN 'CANCELADO' ELSE 'ACTIVO'",text)
        self.assertIn('translate(lower',text);self.assertIn('EXISTS',text)
        self.assertNotIn('"p"."estado"::text',text)
        self.assertEqual(records[0][2],'CANCELADO')

    def test_model_missing_novelty_relations_does_not_invent_active(self):
        from validador_renumeracion.database import source_state_expression
        cursor=MagicMock();cursor.fetchall.return_value=[]
        expression,args=source_state_expression(cursor,'modelo','Modelo Interno',{'t_id':'t_id','estado':'estado'})
        self.assertEqual(sql_text(expression),'NULL::text');self.assertEqual(args,())

    def test_state_survives_policy_recalculation_and_excel_exports(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        proposal,candidates,r1=projected();owner=MaximaDialog();owner.result=r1;parent=CandidateDialog(owner)
        dialog=ProposalDialog(proposal,'Estado desde la fuente',parent)
        try:
            dialog.take_090x.setChecked(True)
            self.assertTrue(all(row['status']=='Generado' for row in dialog.proposal))
            self.assertEqual(dialog.proposal[-1]['predio_state'],'CANCELADO')
            dialog.comparison=compare_proposal(dialog.proposal,[{'line':i,'old':r['old'],'new':r['new']} for i,r in enumerate(dialog.proposal)],True)
            with tempfile.TemporaryDirectory() as directory:
                path=str(Path(directory)/'estado.xlsx')
                with patch('validador_renumeracion.proposal_dialog.QFileDialog.getSaveFileName',return_value=(path,'')):dialog.export()
                book=load_workbook(path,read_only=True)
                self.assertEqual(book['Renumeracion']['C1'].value,'Estado del predio')
                self.assertEqual(book['Renumeracion']['C4'].value,'CANCELADO')
                comparison=list(book['Comparacion'].values)
                column=comparison[0].index('Estado del predio')
                self.assertEqual(comparison[-1][column],'CANCELADO');book.close()
        finally:dialog.close();parent.close();owner.close()
