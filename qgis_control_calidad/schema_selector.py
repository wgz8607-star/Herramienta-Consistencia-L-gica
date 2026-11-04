"""Department / municipality / schema popup, with leaf-only selection."""
from collections import defaultdict
import re
import unicodedata
from qgis.PyQt.QtCore import Qt, QEvent
from qgis.PyQt.QtWidgets import QComboBox, QFrame, QVBoxLayout, QTreeWidget, QTreeWidgetItem


def sort_key(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


def schema_location(name, catalog):
    codes = {code for code in re.findall(r'(?<!\d)\d{5}(?!\d)', name) if code in catalog}
    if len(codes) == 1:
        code = next(iter(codes))
        department, municipality = catalog[code]
        return department, municipality, code
    return None


def matching_schemas(names, catalog, text=''):
    needle = sort_key(text.strip())
    return [name for name in names if needle in sort_key(' '.join((name,) + (schema_location(name, catalog) or ())))]


class SchemaSelector(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.catalog = {}
        self.popup = QFrame(self, Qt.Popup)
        self.popup.setObjectName('schemaTreePopup')
        self.popup.setStyleSheet('QFrame#schemaTreePopup { background: white; border: 1px solid #3FA4F5; } QTreeWidget { background: white; color: #344054; }')
        layout = QVBoxLayout(self.popup)
        layout.setContentsMargins(4,4,4,4)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemClicked.connect(self.choose_item)
        self.tree.installEventFilter(self)
        layout.addWidget(self.tree)

    def rebuild_tree(self):
        self.tree.clear()
        groups = defaultdict(lambda: defaultdict(list))
        unknown = []
        for index in range(self.count()):
            name = self.itemText(index)
            location = schema_location(name, self.catalog)
            if location:
                department, municipality, code = location
                groups[department][(municipality,code)].append(name)
            else:
                unknown.append(name)
        def heading(parent, label):
            item = QTreeWidgetItem(parent, [label])
            item.setFlags(Qt.ItemIsEnabled)
            font = item.font(0); font.setBold(True); item.setFont(0,font)
            return item
        def leaf(parent, name):
            item = QTreeWidgetItem(parent,[name])
            item.setData(0,Qt.UserRole,name)
            item.setToolTip(0,name)
            if name == self.currentText():
                self.tree.setCurrentItem(item)
        for department in sorted(groups,key=sort_key):
            parent = heading(self.tree,department)
            for municipality,code in sorted(groups[department],key=lambda pair:sort_key(pair[0])):
                names = groups[department][(municipality,code)]
                place = heading(parent,f'{municipality} ({code}) · {len(names)} ' + ('esquema' if len(names)==1 else 'esquemas'))
                for name in sorted(names,key=sort_key):
                    leaf(place,name)
        if unknown:
            parent = heading(self.tree,'Sin ubicación identificada')
            for name in sorted(unknown,key=sort_key):
                leaf(parent,name)
        self.tree.expandAll()

    def showPopup(self):
        self.rebuild_tree()
        self.popup.resize(max(460,self.width()),min(480,max(150,(self.count()+5)*25)))
        point = self.mapToGlobal(self.rect().bottomLeft())
        screen = self.screen().availableGeometry()
        point.setX(max(screen.left(),min(point.x(),screen.right()-self.popup.width())))
        if point.y()+self.popup.height()>screen.bottom():
            point.setY(max(screen.top(),self.mapToGlobal(self.rect().topLeft()).y()-self.popup.height()))
        self.popup.move(point)
        self.popup.show()
        self.tree.setFocus()

    def hidePopup(self):
        self.popup.hide()

    def choose_item(self,item,column=0):
        name = item.data(0,Qt.UserRole)
        if name is not None:
            self.setCurrentIndex(self.findText(name))
            self.activated.emit(self.currentIndex())
            self.hidePopup()

    def hideEvent(self,event):
        self.hidePopup()
        super().hideEvent(event)

    def eventFilter(self,watched,event):
        if watched is self.tree and event.type()==QEvent.KeyPress and event.key() in (Qt.Key_Return,Qt.Key_Enter):
            item=self.tree.currentItem()
            if item:
                if item.data(0,Qt.UserRole) is None:
                    item.setExpanded(not item.isExpanded())
                else:
                    self.choose_item(item)
            return True
        return super().eventFilter(watched,event)
