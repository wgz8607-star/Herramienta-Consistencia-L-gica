import unittest
from validador_renumeracion.provisional_style import highlighted_text,BACKGROUND


class ProvisionalStyleTests(unittest.TestCase):
    def test_count_highlighting_escapes_source_text_and_preserves_line_breaks(self):
        value=highlighted_text('Fuente: <base>&datos\nProvisionales: 2.912 · Activos: 2.673')
        self.assertIn('&lt;base&gt;&amp;datos<br/>',value)
        self.assertIn('>Provisionales: 2.912</span>',value)
        self.assertNotIn('>Activos:',value)

    def test_proposal_provisional_column_is_emphasized_without_changing_result_data(self):
        from test_ui import app
        from test_renumbering import generate,old
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        owner=MaximaDialog();parent=CandidateDialog(owner);proposal=generate([old()]);dialog=ProposalDialog(proposal,'Fuente',parent)
        try:
            self.assertIn('>Provisionales en la propuesta: 1</span>',dialog.summary.text())
            tree=dialog.views['Propuesta'];leaf=tree.topLevelItem(0).child(0).child(0)
            old_column=next(index for index,(_,key) in enumerate(dialog.fields['Propuesta']) if key=='old')
            new_column=next(index for index,(_,key) in enumerate(dialog.fields['Propuesta']) if key=='new')
            self.assertTrue(leaf.font(old_column).bold())
            self.assertEqual(leaf.background(old_column).color().name(),BACKGROUND.lower())
            self.assertNotEqual(leaf.background(new_column).color().name(),BACKGROUND.lower())
            self.assertEqual(leaf.text(old_column),proposal[0]['old'])
        finally:dialog.close();parent.close();owner.close()

    def test_excel_highlights_provisional_column_not_definitive(self):
        from openpyxl import Workbook
        from validador_renumeracion.provisional_style import emphasize_workbook
        book=Workbook();sheet=book.active;sheet.append(['Definitivo esperado','Provisional']);sheet.append(['1'*30,'9'*30])
        emphasize_workbook(book)
        self.assertEqual(sheet['B2'].fill.fgColor.rgb,'00FFF1CC')
        self.assertTrue(sheet['B2'].font.bold)
        self.assertNotEqual(sheet['A2'].fill.fgColor.rgb,'00FFF1CC')
        book.close()

    def test_logic_button_opens_explanation_from_main_and_proposal(self):
        from test_ui import app
        from test_renumbering import generate,old
        from unittest.mock import patch
        from validador_renumeracion.dialog import MaximaDialog
        from validador_renumeracion.candidate_dialog import CandidateDialog
        from validador_renumeracion.proposal_dialog import ProposalDialog
        from validador_renumeracion.logic_dialog import RenumberingLogicDialog
        owner=MaximaDialog();parent=CandidateDialog(owner);proposal=ProposalDialog(generate([old()]),'Contexto',parent)
        help_dialog=RenumberingLogicDialog(proposal)
        try:
            with patch('validador_renumeracion.candidate_dialog.show_renumbering_logic') as open_main:
                parent.logic_button.click();open_main.assert_called_once_with(parent)
            with patch('validador_renumeracion.proposal_dialog.show_renumbering_logic') as open_proposal:
                proposal.logic_button.click();open_proposal.assert_called_once_with(proposal)
            text=help_dialog.browser.toPlainText()
            self.assertIn('uno o varios predios de condición 5',text)
            self.assertIn('0900–0909',text)
            self.assertIn('23–30',text)
            self.assertIn('no modifica los datos',text)
        finally:help_dialog.close();proposal.close();parent.close();owner.close()
