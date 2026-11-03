import unittest
from unittest.mock import Mock, patch
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtTest import QTest
from qgis_control_calidad.dialog import ControlCalidadDialog, PersistentSelectionMenu
from test_cica_and_formats import app


class ParameterControlsTests(unittest.TestCase):
    def test_disabled_styles_preserve_enabled_colors(self):
        from qgis.PyQt.QtWidgets import QWidget, QPushButton
        from qgis_control_calidad.button_styles import style_disabled_buttons, DISABLED_STYLE
        parent = QWidget()
        button = QPushButton('Ejecutar', parent)
        button.setStyleSheet('background: #0468A3; color: white;')
        style_disabled_buttons(parent)
        self.assertIn('QPushButton, QToolButton {background: #0468A3;', button.styleSheet())
        self.assertIn(DISABLED_STYLE, button.styleSheet())
        button.setEnabled(False)
        button.setEnabled(True)
        self.assertIn('#0468A3', button.styleSheet())
        style_disabled_buttons(parent)
        self.assertEqual(button.styleSheet().count(DISABLED_STYLE), 1)
        parent.close()

    def test_menu_stays_open_for_mouse_and_keyboard(self):
        menu = PersistentSelectionMenu()
        action = menu.addAction('Administrativas')
        action.setCheckable(True)
        menu.popup(app.activeWindow().pos() if app.activeWindow() else __import__('qgis.PyQt.QtCore', fromlist=['QPoint']).QPoint(10, 10))
        app.processEvents()
        QTest.mouseClick(menu, Qt.LeftButton, pos=menu.actionGeometry(action).center())
        self.assertTrue(action.isChecked())
        self.assertTrue(menu.isVisible())
        menu.setActiveAction(action)
        QTest.keyClick(menu, Qt.Key_Space)
        self.assertFalse(action.isChecked())
        self.assertTrue(menu.isVisible())
        menu.close()

    def test_schema_search_and_reset_close_temporaries(self):
        dialog = ControlCalidadDialog()
        dialog.listed_schemas = ['public', '41206_colombia', '47745_sitionuevo']
        dialog.filter_schemas()
        dialog.schema_search.setText('SITIONUEVO')
        self.assertEqual(dialog.schema.count(), 1)
        self.assertEqual(dialog.schema.itemText(0), '47745_sitionuevo')
        dialog.schema_search.clear()
        self.assertEqual(dialog.schema.count(), 3)
        gdb = Mock(); csv = Mock(); reference = Mock()
        dialog.cica_gdb = gdb
        dialog.cica_references = {'cica_predio': csv}
        dialog.temporary_references = {'R1': reference}
        dialog.general_report_rows = [{'cantidad': 1}]
        dialog.scope_selection = 'urban'
        dialog.scope_prefixes = ('12345678901234567',)
        with patch.object(dialog, 'confirm_review_changes', return_value=True):
            dialog.clear_parameters()
        for item in (gdb, csv, reference):
            item.close.assert_called_once()
        self.assertEqual(dialog.scope_selection, 'all')
        self.assertEqual(dialog.scope_prefixes, ())
        self.assertEqual(dialog.schema.count(), 0)
        self.assertEqual(dialog.environment.currentIndex(), 0)
        self.assertEqual(dialog.general_report_rows, [])
        self.assertIsNone(dialog.cica_gdb)
        self.assertFalse(dialog.run_button.isEnabled())
        dialog.close()

    def test_reset_is_blocked_during_validation(self):
        dialog = ControlCalidadDialog()
        dialog.controls_running = True
        dialog.database.setText('conservar')
        dialog.clear_parameters()
        self.assertEqual(dialog.database.text(), 'conservar')
        dialog.controls_running = False
        dialog.close()
