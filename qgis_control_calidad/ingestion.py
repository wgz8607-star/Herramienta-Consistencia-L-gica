"""Prepare independent CICA CSV snapshots for temporary validation tables."""
from qgis.PyQt.QtWidgets import (
    QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)
from .cica_data import TABLES as CSV_INPUTS, prepare_csv
from .cica_gdb import prepare_gdb


class CicaIngestionDialog(QDialog):
    def __init__(self, parent=None, references=None, geodatabase=None):
        super().__init__(parent)
        self.setWindowTitle('Cargue archivos CICA')
        self.resize(820, 520)
        self.prepared = {}
        self.prepared_gdb = None
        self.existing_gdb = geodatabase
        self.existing = dict(references or {})
        self.files = {}
        layout = QVBoxLayout(self)
        note = QLabel('Seleccione los CSV individualmente y la geodatabase (.gdb o .zip). Los archivos se usarán temporalmente durante la validación, sin modificar los originales. Puede reemplazar un archivo sin volver a seleccionar los demás.')
        note.setWordWrap(True)
        layout.addWidget(note)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); form = QFormLayout(content)
        for label, table in CSV_INPUTS.items():
            field = QLineEdit(); field.setReadOnly(True)
            if table in self.existing:
                ref = self.existing[table]
                field.setText(f'{ref.filename} · {ref.row_count} registros')
            button = QPushButton('Cargar CSV…')
            button.clicked.connect(lambda _=False, key=label: self.choose_csv(key))
            row = QHBoxLayout(); row.addWidget(field, 1); row.addWidget(button)
            form.addRow(label, row); self.files[label] = field
        self.gdb = QLineEdit(); self.gdb.setReadOnly(True)
        if self.existing_gdb:
            self.gdb.setText(f'{self.existing_gdb.filename} · {len(self.existing_gdb.layers)} capas/tablas')
        choose_gdb = QPushButton('Seleccionar geodatabase…')
        choose_gdb.clicked.connect(self.choose_gdb)
        gdb_row = QHBoxLayout(); gdb_row.addWidget(self.gdb, 1); gdb_row.addWidget(choose_gdb)
        form.addRow('Geodatabase CICA', gdb_row)
        scroll.setWidget(content); layout.addWidget(scroll, 1)
        self.status = QLabel('Sin esquema de destino. Los archivos estarán disponibles para las validaciones de esta sesión; los datos de trabajo de cada ejecución se eliminan al finalizarla.')
        self.status.setWordWrap(True); layout.addWidget(self.status)
        buttons = QHBoxLayout(); buttons.addStretch()
        cancel = QPushButton('Cancelar'); cancel.clicked.connect(self.reject)
        apply = QPushButton('Usar archivos temporales'); apply.clicked.connect(self.validate_inputs)
        buttons.addWidget(cancel); buttons.addWidget(apply); layout.addLayout(buttons)

    def choose_csv(self, key):
        path, _ = QFileDialog.getOpenFileName(self, f'Seleccione {key}', '', 'Archivos CSV (*.csv)')
        if not path:
            return
        table = CSV_INPUTS[key]
        self.setEnabled(False)
        try:
            owner = self.parent()
            reference = owner.report_task(prepare_csv, table, path) if owner is not None and hasattr(owner, 'report_task') else prepare_csv(table, path)
        except Exception as error:
            QMessageBox.warning(self, 'No se cargó el CSV', str(error))
            return
        finally:
            self.setEnabled(True)
        previous = self.prepared.get(table)
        self.prepared[table] = reference
        if previous:
            previous.close()
        self.files[key].setText(f'{reference.filename} · {reference.row_count} registros')
        self.status.setText(f'{key}: preparado temporalmente. Use «Usar archivos temporales» para aplicarlo.')

    def choose_gdb(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Seleccione una geodatabase comprimida', '', 'Geodatabase comprimida (*.zip)')
        if not path:
            path = QFileDialog.getExistingDirectory(self, 'Seleccione la carpeta .gdb')
        if not path:
            return
        self.setEnabled(False)
        self.status.setText('Preparando geodatabase temporal…')
        try:
            owner = self.parent()
            prepared = owner.report_task(prepare_gdb, path) if owner is not None and hasattr(owner, 'report_task') else prepare_gdb(path)
        except Exception as error:
            QMessageBox.warning(self, 'No se cargó la geodatabase', str(error))
            return
        finally:
            self.setEnabled(True)
        if self.prepared_gdb:
            self.prepared_gdb.close()
        self.prepared_gdb = prepared
        self.gdb.setText(f'{prepared.filename} · {len(prepared.layers)} capas/tablas')
        self.gdb.setToolTip('\n'.join(f'{layer.source_name} → {name}: {layer.row_count} registros' for name, layer in prepared.layers.items()))
        self.status.setText('Geodatabase preparada. Pulse «Usar archivos temporales» para aplicarla. Si una tabla también tiene CSV seleccionado, se utiliza el CSV.')

    def validate_inputs(self):
        if not (self.prepared or self.existing or self.prepared_gdb or self.existing_gdb):
            QMessageBox.warning(self, 'Sin insumos', 'Seleccione al menos un CSV o una geodatabase.')
            return
        self.accept()

    def take_prepared(self):
        prepared, self.prepared = self.prepared, {}
        return prepared

    def take_geodatabase(self):
        prepared, self.prepared_gdb = self.prepared_gdb, None
        return prepared

    def clear_prepared(self):
        if self.prepared_gdb:
            self.prepared_gdb.close()
            self.prepared_gdb = None
        for reference in self.prepared.values():
            reference.close()
        self.prepared = {}
