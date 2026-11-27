"""Temporary user references for terrain maxima absent from an outdated R1."""
from copy import deepcopy
import re
from qgis.PyQt.QtWidgets import QDialog,QFormLayout,QComboBox,QLabel,QLineEdit,QSpinBox,QPushButton,QHBoxLayout,QMessageBox,QDialogButtonBox
from .candidates import block_name


class MaximumOverridesDialog(QDialog):
    def __init__(self,proposal,reference,current,parent=None):
        super().__init__(parent);self.setWindowTitle('4.2 Máximo adicional por manzana/vereda');self.resize(850,360)
        self.values=deepcopy(current);self.dirty=False;self.loading=False;self.previous_block=None;from .renumbering import terrain_baselines
        self.baselines=terrain_baselines(reference,parent.take_090x.isChecked() if parent is not None and hasattr(parent,'take_090x') else False)
        layout=QFormLayout(self);info=QLabel('Si el R1 perdió temporalidad, indique el máximo de terreno que conoce.\nSe usará el mayor entre el R1 y el adicional, sin modificar el archivo ni la base.');info.setWordWrap(True);layout.addRow(info)
        self.block=QComboBox()
        for code in sorted({row['old'][:17] for row in proposal}):self.block.addItem(block_name(code)+' · '+code,code)
        layout.addRow('Manzana/vereda (1–17)',self.block)
        self.baseline=QLabel();layout.addRow('Máximo en R1 leído',self.baseline)
        self.npn=QLineEdit();self.npn.setPlaceholderText('Opcional: NPN completo del predio máximo, en la misma manzana/vereda');self.npn.setMaxLength(30);layout.addRow('Predio adicional (NPN)',self.npn)
        self.maximum=QSpinBox();self.maximum.setRange(0,9999);layout.addRow('Máximo de terreno adicional',self.maximum)
        self.note=QLineEdit();self.note.setPlaceholderText('Referencia o motivo del ajuste temporal');layout.addRow('Observación',self.note)
        row=QHBoxLayout();add=QPushButton('4.2.1 Añadir / actualizar');add.clicked.connect(self.store);row.addWidget(add);remove=QPushButton('4.2.2 Quitar adicional');remove.clicked.connect(self.remove);row.addWidget(remove);layout.addRow(row)
        self.status=QLabel();layout.addRow(self.status)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Save).setText('4.2.3 Guardar y volver a comparar');buttons.accepted.connect(self.save_and_close);buttons.rejected.connect(self.reject);layout.addRow(buttons)
        self.block.currentIndexChanged.connect(self.select_block);self.npn.textChanged.connect(self.infer_maximum)
        self.npn.textChanged.connect(self.mark_dirty);self.maximum.valueChanged.connect(self.mark_dirty);self.note.textChanged.connect(self.mark_dirty);self.refresh()

    def mark_dirty(self,*_):
        if not self.loading:self.dirty=True

    def select_block(self,*_):
        if self.dirty:
            self.block.blockSignals(True);self.block.setCurrentIndex(self.block.findData(self.previous_block));self.block.blockSignals(False)
            QMessageBox.information(self,'Máximo pendiente','Añada o guarde el máximo actual antes de cambiar de manzana/vereda.');return
        self.refresh()

    def refresh(self,*_):
        self.loading=True
        code=self.block.currentData();data=self.values.get(code,{})
        base=self.baselines.get(code)
        self.baseline.setText(f'{base:04d}' if base is not None else 'Sin referencia R1 para esta manzana/vereda')
        self.npn.setText(data.get('npn',''));self.maximum.setValue(data.get('max_t',base or 0));self.note.setText(data.get('note',''))
        self.status.setText(f'{len(self.values)} manzanas/veredas con máximo adicional temporal.')
        self.previous_block=code;self.loading=False;self.dirty=False

    def infer_maximum(self,value):
        if len(value)==30 and value[17:21].isdigit():self.maximum.setValue(int(value[17:21]))

    def store(self):
        code=self.block.currentData();npn=self.npn.text().strip()
        if npn and (not re.fullmatch(r'[0-9A-Za-z]{30}',npn) or npn[:17]!=code or not npn[17:].isdigit()):
            QMessageBox.warning(self,'Predio máximo no válido','El NPN debe tener 30 caracteres y pertenecer a la manzana/vereda seleccionada.');return False
        if npn and int(npn[17:21])!=self.maximum.value():
            QMessageBox.warning(self,'Máximo no coincide','El máximo debe coincidir con las posiciones 18–21 del NPN indicado.');return False
        self.values[code]={'max_t':self.maximum.value(),'npn':npn,'note':self.note.text().strip()}
        self.status.setText(f'Máximo {self.maximum.value():04d} añadido para {code}. Se recalculará al guardar.');self.dirty=False;return True

    def remove(self):
        self.values.pop(self.block.currentData(),None);self.refresh()

    def save_and_close(self):
        if self.dirty and not self.store():return
        self.accept()
