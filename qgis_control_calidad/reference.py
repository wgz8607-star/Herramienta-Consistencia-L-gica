"""Select local R1 (and optional R2) without publishing database tables."""
from qgis.PyQt.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QProgressBar, QPushButton, QVBoxLayout,
)
from .reference_data import prepare_reference, clean, column_name


class ReferenceDialog(QDialog):
    def __init__(self, parent=None, params_provider=None):
        super().__init__(parent)
        self.references = {}
        self.setWindowTitle('Preparar R1 y R2 temporales')
        self.resize(620, 240)
        layout = QVBoxLayout(self)
        note = QLabel('R1 se prepara localmente. Durante la validación se carga en una tabla temporal; se elimina al cerrar la conexión. R2 es opcional.')
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        self.r1 = self.file_row(form, 'Archivo R1')
        self.r2 = self.file_row(form, 'Archivo R2 (opcional)')
        layout.addLayout(form)
        self.status = QLabel('Seleccione un Excel R1 (.xlsx).')
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        actions = QHBoxLayout()
        self.prepare_button = QPushButton('Preparar referencias temporales')
        self.prepare_button.clicked.connect(self.validate)
        self.accept_button = QPushButton('Aceptar')
        self.accept_button.setEnabled(False)
        self.accept_button.clicked.connect(self.accept)
        actions.addWidget(self.prepare_button)
        actions.addWidget(self.accept_button)
        layout.addLayout(actions)

    def file_row(self, form, label):
        field = QLineEdit()
        field.setReadOnly(True)
        button = QPushButton('Seleccionar')
        button.clicked.connect(lambda: self.choose(field))
        row = QHBoxLayout()
        row.addWidget(field, 1)
        row.addWidget(button)
        form.addRow(label, row)
        return field

    def choose(self, field):
        filename, _ = QFileDialog.getOpenFileName(self, 'Seleccionar referencia Excel', '', 'Excel (*.xlsx)')
        if filename:
            field.setText(filename)
            self.clear_prepared()
            self.accept_button.setEnabled(False)

    def clear_prepared(self):
        for reference in self.references.values():
            reference.close()
        self.references = {}

    def validate(self):
        if not self.r1.text():
            QMessageBox.warning(self, 'Falta R1', 'Seleccione el archivo R1.')
            return
        prepared = {}
        self.prepare_button.setEnabled(False)
        self.progress.setRange(0, 0)
        self.progress.setVisible(True)
        try:
            for kind, field in (('R1', self.r1), ('R2', self.r2)):
                if field.text():
                    self.status.setText('Preparando ' + kind + ' localmente…')
                    QApplication.processEvents()
                    prepared[kind] = prepare_reference(kind, field.text())
        except Exception as error:
            for reference in prepared.values():
                reference.close()
            QMessageBox.warning(self, 'No se prepararon las referencias', str(error))
            return
        finally:
            self.progress.setVisible(False)
            self.prepare_button.setEnabled(True)
        self.clear_prepared()
        self.references = prepared
        self.status.setText(' · '.join(f'{kind}: {reference.row_count} registros preparados' for kind, reference in prepared.items()))
        self.accept_button.setEnabled(True)

    def take_references(self):
        references = self.references
        self.references = {}
        return references

    def done(self, result):
        if result != QDialog.Accepted:
            self.clear_prepared()
        super().done(result)

    clean_excel_value = staticmethod(clean)
    column_name = staticmethod(column_name)
