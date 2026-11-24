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

    def test_grouped_views_display_prefix9_subdivision10_13_and_r1_start(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog,PROPOSAL_FIELDS
        owner=MaximaDialog();parent=CandidateDialog(owner)
        r1=build_maxima([(1,npn(block='0010')),(2,npn(sector='010100',block='0200'))])
        owner.result=r1
        proposal=generate([old(),old(sector='010100')],r1)
        dialog=ProposalDialog(proposal,'Contexto',parent)
        try:
            tree=dialog.views['Propuesta'];self.assertEqual(tree.topLevelItemCount(),1)
            root=tree.topLevelItem(0);self.assertEqual(root.text(0),'1–9: '+old()[:9])
            self.assertEqual(root.childCount(),2)
            first,second=root.child(0),root.child(1)
            self.assertEqual(first.text(0),'10–13: 0000');self.assertEqual(second.text(0),'10–13: 0100')
            base=next(i for i,(_,key) in enumerate(PROPOSAL_FIELDS) if key=='base_m')
            start=next(i for i,(_,key) in enumerate(PROPOSAL_FIELDS) if key=='next_m')
            self.assertEqual(first.text(base),'0010');self.assertEqual(first.text(start),'0011')
            self.assertEqual(second.text(base),'0200');self.assertEqual(second.text(start),'0201')
            dialog.set_column_filter('Propuesta',base,'0200')
            root=tree.topLevelItem(0);self.assertEqual(root.childCount(),1)
            self.assertEqual(root.child(0).text(0),'10–13: 0100')
            dialog.clear_column_filters();self.assertEqual(tree.topLevelItem(0).childCount(),2)
        finally:dialog.close();parent.close();owner.close()

    def test_comparison_hides_non_provisionals_and_combines_header_and_status_filters(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog,COMPARE_FIELDS
        owner=MaximaDialog();parent=CandidateDialog(owner);proposal=generate([old(),old('9003')]);a,b=proposal
        dialog=ProposalDialog(proposal,'Contexto',parent)
        try:
            rows=[{'line':2,'old':a['old'],'new':a['new']},{'line':3,'old':b['old'],'new':b['old']},{'line':4,'old':npn(),'new':npn()}]
            dialog.comparison=compare_proposal(proposal,rows);dialog.tabs.setCurrentIndex(1);dialog.update_filters()
            self.assertEqual(len(dialog.visible_data('Comparación')),2)
            status=next(i for i,(_,key) in enumerate(COMPARE_FIELDS) if key=='status')
            dialog.set_column_filter('Comparación',status,'Diferencia')
            self.assertEqual([row['old'] for row in dialog.visible_data('Comparación')],[b['old']])
            dialog.status_filter.setCurrentIndex(dialog.status_filter.findData('Coincide'))
            self.assertEqual(dialog.views['Comparación'].topLevelItemCount(),0)
            dialog.clear_column_filters();self.assertEqual(len(dialog.visible_data('Comparación')),1)
        finally:dialog.close();parent.close();owner.close()

    def test_export_contains_only_proposal_provisionals_and_group_baselines(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        owner=MaximaDialog();parent=CandidateDialog(owner);proposal=generate([old()]);a=proposal[0]
        dialog=ProposalDialog(proposal,'Contexto',parent)
        try:
            dialog.comparison=compare_proposal(proposal,[{'line':2,'old':a['old'],'new':a['new']},{'line':3,'old':npn(),'new':npn()}])
            with tempfile.TemporaryDirectory() as directory:
                filename=str(Path(directory)/'grupos.xlsx')
                with patch('validador_renumeracion.proposal_dialog.QFileDialog.getSaveFileName',return_value=(filename,'')):dialog.export()
                book=load_workbook(filename,read_only=True)
                self.assertEqual(book['Comparacion'].max_row,2)
                self.assertEqual(book['Comparacion']['A2'].value,a['old'])
                groups=book['Grupos y maximos R1']
                self.assertEqual(groups['B2'].value,a['old'][:9])
                self.assertEqual(groups['C2'].value,a['old'][9:13])
                self.assertEqual(groups['F2'].value,'0010')
                self.assertEqual(groups['G2'].value,'0011');book.close()
        finally:dialog.close();parent.close();owner.close()

    def test_comparison_strict_scope_omits_unchanged_non_provisional_rows(self):
        proposal=generate([old()]);item=proposal[0]
        rows=[{'line':2,'old':item['old'],'new':item['new']},{'line':3,'old':npn(),'new':npn()}]
        result=compare_proposal(proposal,rows,only_provisionals=True)
        self.assertEqual(len(result),1);self.assertEqual(result[0]['status'],'Coincide')
        candidate_rows=[(npn(),)]+[(old(),)]
        r1=build_maxima([(1,npn(block='0010',plot='0020'))])
        self.assertEqual([row['old'] for row in generate_proposal(candidate_rows,r1,'CICA')],[old()])

    def test_optional_090x_condition9_changes_only_terrain_baseline(self):
        from validador_renumeracion.renumbering import terrain_baselines
        r1=build_maxima([(1,npn(block='0010',plot='0042')),(2,npn(block='0010',plot='0903',condition='9'))])
        rows=identify_candidates([(1,old('0010')),(2,old('9001'))],'CICA')['rows']
        snapshot=deepcopy(r1)
        excluded=generate_proposal(rows,r1,'CICA')
        included=generate_proposal(rows,r1,'CICA',True)
        a=next(row for row in excluded if row['old']==old('0010'))
        b=next(row for row in included if row['old']==old('0010'))
        self.assertEqual(a['base_t'],42);self.assertEqual(a['new'][17:21],'0043')
        self.assertEqual(b['base_t'],903);self.assertEqual(b['new'][17:21],'0904')
        self.assertEqual([row['base_m'] for row in excluded],[row['base_m'] for row in included])
        self.assertEqual(r1,snapshot)
        other=build_maxima([(1,npn(block='0010',plot='0903',condition='0')),(2,npn(block='0010',plot='0909',condition='9'))])
        self.assertEqual(terrain_baselines(other)[npn(block='0010')[:17]],903)
        beyond=build_maxima([(1,npn(block='0010',plot='0910',condition='9'))])
        self.assertEqual(terrain_baselines(beyond)[npn(block='0010')[:17]],910)

    def test_only_090x_reference_does_not_invent_zero_and_collisions_remain_pending(self):
        r1=build_maxima([(1,npn(block='0010',plot='0903',condition='9'))])
        rows=identify_candidates([(1,old('0010'))],'CICA')['rows']
        excluded=generate_proposal(rows,r1,'CICA')
        self.assertEqual(excluded[0]['status'],'Pendiente');self.assertIn('090x',excluded[0]['reason'])
        self.assertEqual(generate_proposal(rows,r1,'CICA',True)[0]['new'][17:21],'0904')
        r1=build_maxima([(1,npn(block='0010',plot='0900')),(2,npn(block='0010',plot='0901',condition='9'))])
        rows=identify_candidates([(1,old('0010',condition='9'))],'CICA')['rows']
        proposal=generate_proposal(rows,r1,'CICA')
        self.assertEqual(proposal[0]['status'],'Pendiente');self.assertIn('ya existe',proposal[0]['reason'])

    def test_090x_checkbox_recalculates_existing_comparison_and_export_policy(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        owner=MaximaDialog();parent=CandidateDialog(owner)
        r1=build_maxima([(1,npn(block='0010',plot='0042')),(2,npn(block='0010',plot='0903',condition='9'))]);owner.result=r1
        candidates=identify_candidates([(1,old('0010'))],'CICA')['rows']
        proposal=generate_proposal(candidates,r1,'CICA');dialog=ProposalDialog(proposal,'Contexto',parent)
        try:
            self.assertFalse(dialog.take_090x.isChecked())
            item=proposal[0];dialog.file_rows=[{'line':2,'old':item['old'],'new':item['new']}];dialog.compared=True
            dialog.comparison=compare_proposal(proposal,dialog.file_rows,True)
            dialog.take_090x.setChecked(True)
            self.assertTrue(dialog.applied_090x)
            self.assertEqual(dialog.proposal[0]['new'][17:21],'0904')
            self.assertEqual(dialog.comparison[0]['status'],'Diferencia')
            dialog.take_090x.setChecked(False)
            self.assertEqual(dialog.comparison[0]['status'],'Coincide')
            self.assertEqual(dialog.proposal[0]['new'][17:21],'0043')
            with tempfile.TemporaryDirectory() as directory:
                filename=str(Path(directory)/'policy.xlsx')
                with patch('validador_renumeracion.proposal_dialog.QFileDialog.getSaveFileName',return_value=(filename,'')):dialog.export()
                book=load_workbook(filename,read_only=True)
                summary=dict(book['Resumen'].iter_rows(values_only=True))
                self.assertEqual(summary['Tomar terrenos 090x condición 9 como máximos R1'],'No');book.close()
        finally:dialog.close();parent.close();owner.close()
