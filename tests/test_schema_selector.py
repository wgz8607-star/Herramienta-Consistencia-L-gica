import unittest
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtTest import QTest
from qgis_control_calidad.schema_selector import SchemaSelector, schema_location, matching_schemas
from qgis_control_calidad.dialog import ControlCalidadDialog
from test_temporary_references import app

CATALOG={'68575':('Santander','Puerto Wilches'),'68190':('Santander','Cimitarra'),'44110':('La Guajira','El Molino')}
NAMES=['o_68575_00_01_20261030_l2','o_68575_actualizacion','o_68190_00_01_20261015','gua_44110_2026','public','otro_99999','largo_1685756']


class SchemaSelectorTests(unittest.TestCase):
    def test_location_requires_one_recognized_code_and_preserves_leading_zeroes(self):
        self.assertEqual(schema_location(NAMES[0],CATALOG),('Santander','Puerto Wilches','68575'))
        self.assertIsNone(schema_location('largo_1685756',CATALOG))
        self.assertIsNone(schema_location('o_99999',CATALOG))
        self.assertIsNone(schema_location('o_68575_68190',CATALOG))
        self.assertEqual(schema_location('o_08421',{'08421':('Atlántico','Luruaco')})[2],'08421')

    def test_search_supports_schema_divipola_department_municipality_and_accents(self):
        self.assertEqual(matching_schemas(NAMES,CATALOG,'Santander'),NAMES[:3])
        self.assertEqual(matching_schemas(NAMES,CATALOG,'puerto wilches'),NAMES[:2])
        self.assertEqual(matching_schemas(NAMES,CATALOG,'68575'),NAMES[:2]+['largo_1685756'])
        self.assertEqual(matching_schemas(NAMES,CATALOG,'actualizacion'),[NAMES[1]])
        self.assertEqual(matching_schemas(['o_08421'],{'08421':('Atlántico','Luruaco')},'atlantico'),['o_08421'])
        self.assertEqual(matching_schemas(NAMES,CATALOG,''),NAMES)
        self.assertEqual(matching_schemas(NAMES,CATALOG,'inexistente'),[])

    def test_tree_groups_counts_unknowns_and_only_schema_leaves_select(self):
        widget=SchemaSelector();self.addCleanup(widget.close)
        widget.catalog=CATALOG;widget.addItems(NAMES);widget.setCurrentIndex(-1)
        widget.rebuild_tree()
        roots={widget.tree.topLevelItem(i).text(0):widget.tree.topLevelItem(i) for i in range(widget.tree.topLevelItemCount())}
        self.assertEqual(set(roots),{'La Guajira','Santander','Sin ubicación identificada'})
        santander=roots['Santander']
        places={santander.child(i).text(0):santander.child(i) for i in range(santander.childCount())}
        place=places['Puerto Wilches (68575) · 2 esquemas']
        for header in (santander,place,roots['Sin ubicación identificada']):
            self.assertFalse(header.flags() & Qt.ItemIsSelectable)
            widget.choose_item(header)
            self.assertEqual(widget.currentText(),'')
        self.assertEqual(roots['Sin ubicación identificada'].childCount(),3)
        leaf=place.child(0)
        self.assertTrue(leaf.flags() & Qt.ItemIsSelectable)
        selected=[];widget.currentTextChanged.connect(selected.append)
        widget.choose_item(leaf)
        self.assertEqual(widget.currentText(),leaf.data(0,Qt.UserRole))
        self.assertEqual(selected,[leaf.data(0,Qt.UserRole)])

    def test_popup_keyboard_selects_leaf_and_escape_closes(self):
        widget=SchemaSelector();self.addCleanup(widget.close)
        widget.catalog=CATALOG;widget.addItems(NAMES);widget.show();widget.showPopup()
        parent=widget.tree.topLevelItem(0)
        place=parent.child(0);leaf=place.child(0)
        widget.tree.setCurrentItem(leaf)
        QTest.keyClick(widget.tree,Qt.Key_Return)
        self.assertEqual(widget.currentText(),leaf.data(0,Qt.UserRole))
        self.assertFalse(widget.popup.isVisible())
        widget.showPopup()
        QTest.keyClick(widget.tree,Qt.Key_Escape)
        app.processEvents()
        self.assertFalse(widget.popup.isVisible())

    def test_filter_clears_hidden_selection_and_preserves_raw_schema_for_validation(self):
        widget=ControlCalidadDialog();self.addCleanup(widget.close)
        widget.schema.catalog=CATALOG;widget.listed_schemas=NAMES;widget.filter_schemas()
        widget.schema.setCurrentText(NAMES[0])
        self.assertEqual(widget.validation_schema(),NAMES[0])
        widget.schema_search.setText('Puerto Wilches')
        self.assertEqual(widget.schema.count(),2)
        self.assertEqual(widget.validation_schema(),NAMES[0])
        widget.schema_search.setText('El Molino')
        self.assertEqual(widget.schema.count(),1)
        self.assertEqual(widget.validation_schema(),'')
        widget.schema.setCurrentIndex(0)
        self.assertEqual(widget.validation_schema(),'gua_44110_2026')
        widget.schema_search.clear()
        self.assertEqual(widget.schema.count(),len(NAMES))
