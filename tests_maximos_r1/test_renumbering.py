import unittest,tempfile
from pathlib import Path
from copy import deepcopy
from openpyxl import Workbook,load_workbook
from unittest.mock import patch
from test_maximos import npn
from validador_renumeracion.core import build_maxima
from validador_renumeracion.candidates import identify_candidates
from validador_renumeracion.renumbering import generate_proposal,compare_proposal,read_comparison


def old(block='9001',plot='9001',condition='0',suffix='00000000',sector='010000',zone='01'):
    return npn(zone=zone,sector=sector,block=block,plot=plot,condition=condition)[:22]+suffix


def generate(values,reference=None,model='CICA'):
    r1=reference or build_maxima([(1,npn(block='0010',plot='0020'))])
    candidates=identify_candidates(enumerate(values,1),model)
    return generate_proposal(candidates['rows'],r1,model)


class RenumberingTests(unittest.TestCase):
    def test_new_blocks_and_plots_sort_provisionals_without_inheriting_gaps(self):
        values=[old('9008','9009'),old('9001','9009'),old('9001','9002')]
        proposal=generate(values);by_old={r['old']:r for r in proposal}
        self.assertEqual(by_old[old('9001','9002')]['new'][13:21],'00110001')
        self.assertEqual(by_old[old('9001','9009')]['new'][13:21],'00110002')
        self.assertEqual(by_old[old('9008','9009')]['new'][13:21],'00120001')
        self.assertEqual(proposal,generate(list(reversed(values))+[values[0]]))

    def test_maximum_block_is_scoped_to_prefix13(self):
        r1=build_maxima([(1,npn(block='0010')),(2,npn(sector='020000',block='0200'))])
        proposal=generate([old(),old(sector='020000')],r1)
        self.assertEqual([r['new'][13:17] for r in proposal],['0011','0201'])

    def test_existing_block_terrain_max_and_condition2_pair(self):
        a=old('0010','9003',condition='0');b=old('0010','9003',condition='2')
        c=old('0010','9009')
        proposal=generate([c,b,a]);by_old={r['old']:r for r in proposal}
        self.assertEqual(by_old[a]['new'][17:21],'0021')
        self.assertEqual(by_old[a]['new'][:21],by_old[b]['new'][:21])
        self.assertEqual(by_old[c]['new'][17:21],'0022')
        self.assertEqual(by_old[b]['new'][21:],'2'+'00000000')

    def test_ph_and_condominium_share_one_terrain_and_preserve_suffixes(self):
        values=[old('0010','9001',c,suffix) for c in ('8',) for suffix in ('00000001','00000002')]
        values += [old('0010','9003','9',suffix) for suffix in ('00000000','01010001','01010002')]
        values.append(old('0010','9003','2'))
        proposal=generate(values)
        self.assertTrue(all(r['status']=='Generado' for r in proposal))
        self.assertEqual({r['new'][17:21] for r in proposal if r['old'][17:21]=='9001'},{'0021'})
        self.assertEqual({r['new'][17:21] for r in proposal if r['old'][17:21]=='9003'},{'0022'})
        self.assertTrue(all(r['new'][21:]==r['old'][21:] for r in proposal))

    def test_model_letters_including_letters_other_than_a_b(self):
        proposal=generate([old('Z010','A009'),old('A003','Z999')],model='Modelo Interno')
        self.assertEqual([r['new'][13:17] for r in proposal],['0011','0012'])
        self.assertTrue(all(r['new'][17:21]=='0001' for r in proposal))

    def test_missing_reference_exhaustion_and_ambiguous_repetitions_are_pending(self):
        missing=generate([old(sector='990000')])[0]
        self.assertEqual(missing['new'],'');self.assertIn('Sin referencia',missing['reason'])
        missing=generate([old('0030')])[0];self.assertEqual(missing['status'],'Pendiente')
        maxed=build_maxima([(1,npn(block='9999',plot='9999'))])
        self.assertIn('agotado',generate([old()],maxed)[0]['reason'])
        maxed=build_maxima([(1,npn(block='0010',plot='9999'))])
        self.assertIn('agotado',generate([old('0010')],maxed)[0]['reason'])
        duplicate=[old('0010','9001',suffix='00000001'),old('0010','9001',suffix='00000002')]
        self.assertTrue(all(r['status']=='Pendiente' for r in generate(duplicate)))
        duplicate=[old('0010','9001','2',suffix=s) for s in ('00000001','00000002')]
        self.assertTrue(all(r['status']=='Pendiente' for r in generate(duplicate)))

    def test_compare_classifies_mismatch_missing_duplicate_and_out_of_scope(self):
        proposal=generate([old('9001'),old('9003'),old('9008')]);a,b,c=proposal
        rows=[{'line':2,'old':a['old'],'new':a['new']},{'line':3,'old':b['old'],'new':b['old']},{'line':4,'old':npn(),'new':npn()}]
        result=compare_proposal(proposal,rows)
        self.assertEqual({r['status'] for r in result},{'Coincide','Diferencia','Falta en archivo','Sin cambio fuera del alcance'})
        self.assertTrue(all(r['status']=='Provisional duplicado en archivo' for r in compare_proposal([a],[rows[0],rows[0]])))
        rows=[{'line':2,'old':a['old'],'new':a['new']},{'line':3,'old':b['old'],'new':a['new']}]
        self.assertTrue(all(r['status']=='Definitivo duplicado en archivo' for r in compare_proposal([a,b],rows)))
        changed=a['new'][:21]+'9'+a['new'][22:]
        self.assertIn('condición',compare_proposal([a],[{'line':2,'old':a['old'],'new':changed}])[0]['reason'])

    def test_pending_is_not_approved_even_if_file_supplies_a_number(self):
        proposal=generate([old(sector='990000')])
        result=compare_proposal(proposal,[{'line':2,'old':proposal[0]['old'],'new':npn()}])
        self.assertEqual(result[0]['status'],'Pendiente de generar')

    def test_excel_reader_keeps_text_and_reports_numeric_or_invalid_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'input.xlsx';book=Workbook();sheet=book.active;sheet.title='Datos'
            proposal=generate([old()])[0]
            sheet.append(['Número predial nuevo','Número predial provisional'])
            sheet.append([proposal['new'],proposal['old']]);sheet.append([123,proposal['old']]);sheet.append(['incorrecto','otro']);book.save(path);book.close()
            before=path.read_bytes();rows,invalid=read_comparison(path,'Datos')
            self.assertEqual(rows[0]['old'],proposal['old']);self.assertEqual(len(invalid),2)
            self.assertEqual(path.read_bytes(),before)

    def test_scope_filters_generation_and_enables_only_with_matching_r1(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        parent=MaximaDialog();dialog=CandidateDialog(parent)
        try:
            dialog.result=identify_candidates([(1,old()),(2,old(zone='00'))],'CICA');dialog.build_scope();dialog.render_candidate_statistics()
            self.assertFalse(dialog.propose_button.isEnabled())
            parent.result=build_maxima([(1,npn())]);dialog._r1_code='41020'
            dialog.scope_boxes['00'].setChecked(False)
            self.assertEqual(len(dialog.selected_candidate_rows()),1)
            self.assertEqual(dialog.selected_candidate_rows()[0][0][5:7],'01')
            self.assertTrue(dialog.propose_button.isEnabled())
            dialog.scope_boxes['01'].setChecked(False);self.assertFalse(dialog.propose_button.isEnabled())
        finally:dialog.close();parent.close()

    def test_proposal_dialog_export_uses_a_new_b_provisional_and_audit_context(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        owner=MaximaDialog();parent=CandidateDialog(owner);proposal=generate([old()]);dialog=ProposalDialog(proposal,'Fuente CICA · R1 y corte de prueba',parent)
        try:
            with tempfile.TemporaryDirectory() as directory:
                filename=str(Path(directory)/'propuesta.xlsx')
                with patch('validador_renumeracion.proposal_dialog.QFileDialog.getSaveFileName',return_value=(filename,'')):dialog.export()
                book=load_workbook(filename,read_only=True)
                self.assertEqual(book['Renumeracion']['A2'].value,proposal[0]['new'])
                self.assertEqual(book['Renumeracion']['B2'].value,proposal[0]['old'])
                self.assertEqual(book['Renumeracion']['A2'].data_type,'s')
                self.assertIn('R1 y corte',book['Resumen']['B2'].value);book.close()
        finally:dialog.close();parent.close();owner.close()

    def test_condition2_can_share_with_each_agreed_base_condition(self):
        for condition in '03489':
            proposal=generate([old('0010','9001',condition),old('0010','9001','2')])
            self.assertTrue(all(r['status']=='Generado' for r in proposal))
            self.assertEqual(len({r['new'][:21] for r in proposal}),1)

    def test_comparison_is_cleared_when_workbook_sheet_changes(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        owner=MaximaDialog();parent=CandidateDialog(owner);dialog=ProposalDialog(generate([old()]),'Contexto',parent)
        try:
            dialog.sheet.addItems(['Uno','Dos']);dialog.comparison=[{'status':'Coincide'}]
            dialog.sheet.setCurrentIndex(1)
            self.assertEqual(dialog.comparison,[])
        finally:dialog.close();parent.close();owner.close()
