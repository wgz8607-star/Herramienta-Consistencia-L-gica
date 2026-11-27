import unittest,tempfile
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from openpyxl import Workbook
from test_maximos import npn
from test_renumbering import old
from validador_renumeracion.candidates import identify_candidates
from validador_renumeracion.core import build_maxima
from validador_renumeracion.renumbering import generate_proposal,compare_proposal


class WorkflowOptionsTests(unittest.TestCase):
    def test_seven_eight_are_independent_and_nine_is_always_provisional(self):
        from test_ui import app
        from validador_renumeracion.cica_options import CicaProvisionalOptions
        dialog=CicaProvisionalOptions()
        try:
            values=[npn(block='7001'),npn(plot='8001'),npn(block='9001')]
            for seven,eight,expected in [(False,False,'9'),(True,False,'79'),(False,True,'89'),(True,True,'789')]:
                dialog.seven.setChecked(seven);dialog.eight.setChecked(eight)
                self.assertEqual(dialog.prefixes(),expected)
                result=identify_candidates(enumerate(values), 'CICA',dialog.prefixes())
                self.assertEqual(len(result['rows']),1+int(seven)+int(eight))
        finally:dialog.close()

    def test_generation_respects_series_as_ordinary_block_or_preserved_terrain(self):
        r1=build_maxima([(1,npn(block='7001',plot='0020'))])
        values=[old('7001','9001'),old('9001','8001')]
        rows=identify_candidates(enumerate(values),'CICA','9')['rows']
        proposal=generate_proposal(rows,r1,'CICA',cica_prefixes='9');by_old={r['old']:r for r in proposal}
        self.assertEqual(by_old[values[0]]['new'][13:21],'70010021')
        self.assertEqual(by_old[values[1]]['new'][17:21],'8001')
        self.assertTrue(by_old[values[1]]['terrain_preserved'])

    def test_cica_confirmation_precedes_source_read_and_cancel_does_not_read(self):
        from test_ui import app
        from qgis.PyQt.QtWidgets import QDialog
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        owner=MaximaDialog();dialog=CandidateDialog(owner)
        try:
            dialog.cica_municipality.addItem('Algeciras','41020')
            with patch('validador_renumeracion.cica_options.CicaProvisionalOptions.exec_',return_value=QDialog.Rejected),patch('validador_renumeracion.candidate_dialog.source_records') as read:
                dialog.load();read.assert_not_called()
            records=[(1,npn(block='7001'),'ACTIVO'),(2,npn(plot='8001'),'ACTIVO'),(3,npn(block='9001'),'ACTIVO')]
            with patch('validador_renumeracion.cica_options.CicaProvisionalOptions.exec_',return_value=QDialog.Accepted),patch('validador_renumeracion.cica_options.CicaProvisionalOptions.prefixes',return_value='79'),patch.object(dialog,'params',return_value={'dbname':'sentencias'}),patch('validador_renumeracion.candidate_dialog.source_records',return_value=records):dialog.load()
            self.assertEqual(dialog.cica_prefixes,'79');self.assertEqual(len(dialog.result['rows']),2)
            self.assertIn('7xxx, 9xxx',dialog.origin)
        finally:dialog.close();owner.close()

    def test_temporary_r1_is_loaded_inside_plugin_filtered_by_municipality_without_database(self):
        from test_ui import app
        from qgis.PyQt.QtWidgets import QDialog
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        owner=MaximaDialog();dialog=CandidateDialog(owner)
        try:
            dialog.cica_municipality.addItem('Algeciras','41020')
            self.assertEqual(dialog.r1_mode.currentIndex(),0)
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'r1.xlsx';book=Workbook();book.active.title='R1';book.active.append(['numero_predial']);book.active.append([npn(plot='0020')]);book.active.append([npn(municipality='25377',plot='9999')]);book.save(path);book.close();before=path.read_bytes()
                with patch('validador_renumeracion.candidate_dialog.QFileDialog.getOpenFileName',return_value=(str(path),'')),patch('validador_renumeracion.temporary_r1.TemporaryR1Dialog.exec_',return_value=QDialog.Accepted),patch('validador_renumeracion.repository.repository_params',side_effect=AssertionError('No se debe consultar la base')):
                    dialog.read_selected_r1()
                self.assertEqual(dialog._r1_code,'41020');self.assertEqual(owner.result.unique_npns,1)
                self.assertEqual(owner.result.blocks[0]['max_t'],'0020')
                self.assertIn('R1 temporal',owner.origin);self.assertIn('omitidos: 1',owner.origin)
                self.assertEqual(before,path.read_bytes());self.assertTrue(dialog.maxima_button.isEnabled())
                dialog.r1_mode.setCurrentIndex(1)
                self.assertIsNone(owner.result);self.assertFalse(dialog.maxima_button.isEnabled())
        finally:dialog.close();owner.close()

    def test_terrain_override_uses_larger_reference_and_does_not_change_r1(self):
        r1=build_maxima([(1,npn(block='0010',plot='0020'))]);snapshot=deepcopy(r1)
        rows=identify_candidates([(1,old('0010'),'ACTIVO')],'CICA')['rows'];block=old('0010')[:17]
        proposal=generate_proposal(rows,r1,'CICA',terrain_overrides={block:{'max_t':45,'npn':'','note':'Posterior al corte'}})
        self.assertEqual(proposal[0]['new'][17:21],'0046');self.assertEqual(proposal[0]['r1_base_t'],20)
        self.assertEqual(proposal[0]['override_t'],45);self.assertEqual(proposal[0]['override_note'],'Posterior al corte')
        self.assertEqual(generate_proposal(rows,r1,'CICA',terrain_overrides={block:10})[0]['new'][17:21],'0021')
        self.assertEqual(r1,snapshot)
        missing=identify_candidates([(1,old('0030'),'ACTIVO')],'CICA')['rows'];other=old('0030')[:17]
        self.assertEqual(generate_proposal(missing,r1,'CICA',terrain_overrides={other:7})[0]['new'][17:21],'0008')

    def test_override_save_recompares_loaded_file_without_reloading_it(self):
        from test_ui import app
        from qgis.PyQt.QtWidgets import QDialog
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        owner=MaximaDialog();parent=CandidateDialog(owner);r1=build_maxima([(1,npn(block='0010',plot='0020'))]);owner.result=r1
        rows=identify_candidates([(1,old('0010'),'ACTIVO')],'CICA')['rows'];proposal=generate_proposal(rows,r1,'CICA');dialog=ProposalDialog(proposal,'Contexto',parent)
        try:
            dialog.file_rows=[{'line':2,'old':proposal[0]['old'],'new':proposal[0]['new']}];dialog.compared=True;dialog.comparison=compare_proposal(proposal,dialog.file_rows,True)
            values={old('0010')[:17]:{'max_t':45,'npn':'','note':'Actualización'}}
            with patch('validador_renumeracion.maximum_overrides.MaximumOverridesDialog') as editor:
                editor.return_value.exec_.return_value=QDialog.Accepted;editor.return_value.values=values
                dialog.edit_maximum_overrides()
            self.assertEqual(dialog.proposal[0]['new'][17:21],'0046')
            self.assertEqual(dialog.comparison[0]['status'],'Diferencia')
            self.assertEqual(dialog.file_rows[0]['new'][17:21],'0021')
        finally:dialog.close();parent.close();owner.close()

    def test_override_editor_accepts_maximum_predio_and_save_applies_unsaved_edit(self):
        from test_ui import app
        from qgis.PyQt.QtWidgets import QDialog
        from validador_renumeracion.maximum_overrides import MaximumOverridesDialog
        r1=build_maxima([(1,npn(block='0010',plot='0020'))]);rows=identify_candidates([(1,old('0010'),'ACTIVO')],'CICA')['rows'];proposal=generate_proposal(rows,r1,'CICA')
        dialog=MaximumOverridesDialog(proposal,r1,{})
        try:
            dialog.npn.setText(npn(block='0010',plot='0045'));dialog.note.setText('Predio posterior')
            self.assertEqual(dialog.maximum.value(),45)
            dialog.save_and_close();self.assertEqual(dialog.result(),QDialog.Accepted)
            self.assertEqual(dialog.values[old('0010')[:17]]['max_t'],45)
            self.assertEqual(dialog.values[old('0010')[:17]]['npn'],npn(block='0010',plot='0045'))
        finally:dialog.close()

    def test_primary_buttons_follow_numbered_sequence(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        owner=MaximaDialog();parent=CandidateDialog(owner);dialog=ProposalDialog([], 'Contexto',parent)
        try:
            self.assertTrue(parent.cica_lookup.text().startswith('1.'))
            self.assertTrue(parent.r1_button.text().startswith('2.'))
            self.assertTrue(parent.read.text().startswith('3.'))
            self.assertTrue(parent.propose_button.text().startswith('4.'))
            self.assertTrue(dialog.browse.text().startswith('5.'))
            self.assertTrue(dialog.compare_button.text().startswith('6.'))
        finally:dialog.close();parent.close();owner.close()

    def test_recalculation_preserves_cica_policy_and_manual_maximum_together(self):
        from test_ui import app
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        owner=MaximaDialog();parent=CandidateDialog(owner);parent.cica_prefixes='9'
        r1=build_maxima([(1,npn(block='7001',plot='0020')),(2,npn(block='7001',plot='0903',condition='9'))]);owner.result=r1
        rows=identify_candidates([(1,old('7001'),'ACTIVO')],'CICA','9')['rows']
        dialog=ProposalDialog(generate_proposal(rows,r1,'CICA',cica_prefixes='9'),'Contexto',parent)
        try:
            dialog.terrain_overrides={old('7001')[:17]:{'max_t':45,'npn':'','note':'Nuevo máximo'}}
            dialog.recalculate(False)
            self.assertEqual(dialog.proposal[0]['new'][13:21],'70010046')
            dialog.take_090x.setChecked(True)
            self.assertEqual(dialog.proposal[0]['new'][13:21],'70010904')
            self.assertEqual(dialog.proposal[0]['override_t'],45)
            dialog.take_090x.setChecked(False)
            self.assertEqual(dialog.proposal[0]['new'][13:21],'70010046')
        finally:dialog.close();parent.close();owner.close()
