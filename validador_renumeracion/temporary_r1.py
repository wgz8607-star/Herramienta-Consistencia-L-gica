"""In-plugin temporary R1 file selection, never uploads to PostgreSQL."""
from pathlib import Path
from qgis.PyQt.QtWidgets import QDialog,QFormLayout,QComboBox,QLabel,QDialogButtonBox,QMessageBox
from openpyxl import load_workbook
from .readers import inspect_excel


class TemporaryR1Dialog(QDialog):
    def __init__(self,filename,parent=None):
        super().__init__(parent);self.filename=filename;self.header=1;self.valid=False
        self.setWindowTitle('Cargar R1 temporal en el plugin');self.resize(650,220)
        layout=QFormLayout(self);layout.addRow('Archivo',QLabel(Path(filename).name))
        self.sheet=QComboBox();self.column=QComboBox();layout.addRow('Hoja',self.sheet);layout.addRow('Columna número predial',self.column)
        self.buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);layout.addRow(self.buttons)
        self.buttons.button(QDialogButtonBox.Ok).setText('2.1 Leer archivo');self.buttons.accepted.connect(self.accept);self.buttons.rejected.connect(self.reject)
        if Path(filename).suffix.lower()=='.xlsx':
            book=load_workbook(filename,read_only=True,data_only=True)
            try:names=book.sheetnames
            finally:book.close()
            self.sheet.addItems(names)
            self.sheet.currentTextChanged.connect(self.update_column)
            selected=next((name for name in names if name.casefold()=='r1'),names[0]);self.sheet.setCurrentText(selected);self.update_column()
        else:
            self.sheet.addItem('TXT estándar R1');self.column.addItem('Posiciones 1–30',0);self.sheet.setEnabled(False);self.column.setEnabled(False);self.valid=True
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(self.valid)

    def update_column(self,*_):
        self.column.clear();self.valid=False
        try:
            _,_,self.header,headers,index=inspect_excel(self.filename,self.sheet.currentText())
            for number,header in enumerate(headers):self.column.addItem(f'{number+1}: {header}',number)
            self.column.setCurrentIndex(index);self.valid=True
        except Exception as error:
            self.column.addItem('No se encontró columna predial');self.column.setToolTip(str(error))
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(self.valid)
