"""Prepare independent CICA CSV snapshots for temporary validation tables."""
from qgis.PyQt.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)
from .cica_data import TABLES as CSV_INPUTS, prepare_csv, prepare_repository_cica, predio_status_summary, read_repository_cica_date
from .cica_gdb import prepare_gdb


class CicaIngestionDialog(QDialog):
    def __init__(self, parent=None, references=None, geodatabase=None):
        super().__init__(parent)
        self.setWindowTitle('Seleccionar fuente de datos CICA')
        self.replace_references = False
        self.resize(820, 520)
        self.prepared = {}
        self.prepared_gdb = None
        self.existing_gdb = geodatabase
        self.existing = dict(references or {})
        self.files = {}
        self.summary_cache = {}
        layout = QVBoxLayout(self)
        note = QLabel('Seleccione los CSV individualmente y la geodatabase (.gdb o .zip). Los archivos se usarán temporalmente durante la validación, sin modificar los originales. Puede reemplazar un archivo sin volver a seleccionar los demás.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.source_mode = QComboBox()
        self.source_mode.addItems(['Archivos CSV del usuario', 'sentencias.snc_cica_copy'])
        layout.addWidget(self.source_mode)
        self.repository_date = QLabel()
        self.repository_date.setWordWrap(True)
        self.repository_date.setStyleSheet('QLabel { background: #EAF2FA; color: #0066B3; padding: 8px; border-radius: 5px; }')
        self.repository_date.hide()
        layout.addWidget(self.repository_date)
        self.read_repository = QPushButton('Leer tablas de sentencias.snc_cica_copy')
        self.read_repository.clicked.connect(self.choose_repository)
        self.read_repository.setVisible(False)
        layout.addWidget(self.read_repository)
        self.source_mode.currentIndexChanged.connect(self.change_source_mode)
        self.csv_buttons = []
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); form = QFormLayout(content)
        for label, table in CSV_INPUTS.items():
            field = QLineEdit(); field.setReadOnly(True)
            if table in self.existing:
                ref = self.existing[table]
                field.setText(f'{ref.filename} · {ref.row_count} registros')
            button = QPushButton('Cargar CSV…')
            self.csv_buttons.append(button)
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
        self.predio_summary = QLabel()
        self.predio_summary.setWordWrap(True)
        self.predio_summary.setStyleSheet('QLabel { background: #EAF5EE; color: #217346; border: 1px solid #B8DAC5; border-radius: 6px; padding: 10px; }')
        layout.addWidget(self.predio_summary)
        self.status = QLabel('Sin esquema de destino. Los archivos estarán disponibles para las validaciones de esta sesión; los datos de trabajo de cada ejecución se eliminan al finalizarla.')
        self.status.setWordWrap(True); layout.addWidget(self.status)
        buttons = QHBoxLayout(); buttons.addStretch()
        cancel = QPushButton('Cancelar'); cancel.clicked.connect(self.reject)
        apply = QPushButton('Usar fuente de datos'); apply.clicked.connect(self.validate_inputs)
        buttons.addWidget(cancel); buttons.addWidget(apply); layout.addLayout(buttons)
        self.update_predio_summary()

    def update_predio_summary(self):
        repository = self.source_mode.currentIndex() == 1
        snapshot = self.prepared.get('cica_predio')
        if snapshot is None and not repository:
            snapshot = self.existing.get('cica_predio')
        if snapshot is None and not repository:
            gdb = self.prepared_gdb or self.existing_gdb
            snapshot = gdb.layers.get('cica_predio') if gdb else None
        if snapshot is None:
            self.predio_summary.setText('Resumen general de predios: lea las tablas del esquema.' if repository else 'Resumen general de predios: cargue Predio (CSV) o una GDB con cica_predio.')
            return
        source = 'sentencias.snc_cica_copy · cica_predio' if repository else snapshot.filename if hasattr(snapshot, 'filename') else 'Geodatabase · cica_predio'
        self.predio_summary.setText('Calculando predios activos y cancelados…')
        self.setEnabled(False)
        try:
            key = str(snapshot.csv_path)
            if key not in self.summary_cache:
                owner = self.parent()
                self.summary_cache[key] = owner.report_task(predio_status_summary, snapshot) if owner is not None and hasattr(owner, 'report_task') else predio_status_summary(snapshot)
            counts = self.summary_cache[key]
            if counts is None:
                text = 'Estado no disponible: cica_predio no contiene el campo estado.'
            else:
                number = lambda value: f'{value:,}'.replace(',', '.')
                text = f"Predios activos: {number(counts['active'])} · Predios cancelados: {number(counts['cancelled'])}"
                if counts['other']:
                    text += f" · Otros estados o sin estado: {number(counts['other'])}"
            self.predio_summary.setText(source + '\n' + text + '\nTotales generales, sin filtros. Conteo de registros de cica_predio.')
        except Exception as error:
            self.predio_summary.setText('Estadística general no disponible: ' + str(error))
        finally:
            self.setEnabled(True)

    def change_source_mode(self, index):
        for reference in self.prepared.values():
            reference.close()
        self.prepared = {}
        self.replace_references = False
        for label, table in CSV_INPUTS.items():
            ref = self.existing.get(table)
            self.files[label].setText(f'{ref.filename} · {ref.row_count} registros' if ref else '')
        self.read_repository.setVisible(index == 1)
        self.repository_date.setVisible(index == 1)
        if index == 1:
            self.refresh_repository_date()
        for button in self.csv_buttons:
            button.setEnabled(index == 0)
        self.update_predio_summary()

    def refresh_repository_date(self, params=None):
        self.repository_date.setText('Consultando fecha de marca de la copia espejo…')
        owner = self.parent()
        if owner is None or not hasattr(owner, 'repository_connection_params'):
            self.repository_date.setText('Fecha de marca: no disponible. Requiere conexión a sentencias.')
            return
        params = params or owner.repository_connection_params()
        if not params:
            self.repository_date.setText('Fecha de marca: no disponible. Falta acceso a sentencias.')
            return
        self.setEnabled(False)
        try:
            value = owner.report_task(read_repository_cica_date, params)
            if value is None:
                message = 'Fecha de marca: sin fecha registrada.'
            else:
                date = value.strftime('%d/%m/%Y · %H:%M:%S %Z').strip() if hasattr(value, 'hour') else value.strftime('%d/%m/%Y') if hasattr(value, 'strftime') else str(value)
                message = 'Última fecha de marca de la copia espejo: ' + date
            self.repository_date.setText(message + '\nOrigen: sentencias.snc_cica_crudo.control · fecha_marca')
        except Exception as error:
            self.repository_date.setText('Fecha de marca no disponible: ' + str(error))
        finally:
            self.setEnabled(True)

    def choose_repository(self):
        owner = self.parent()
        params = owner.repository_connection_params()
        if not params:
            return
        self.setEnabled(False)
        self.status.setText('Leyendo las siete tablas de sentencias.snc_cica_copy…')
        try:
            prepared = owner.report_task(prepare_repository_cica, params)
            for reference in self.prepared.values():
                reference.close()
            self.prepared = prepared
            self.replace_references = True
            for label, table in CSV_INPUTS.items():
                ref = prepared[table]
                self.files[label].setText(f'{ref.filename} · {ref.row_count} registros')
            self.refresh_repository_date(params)
            self.update_predio_summary()
            self.status.setText('Tablas leídas. Puede agregar la GDB y pulsar «Usar fuente de datos». No se modifica el esquema de origen.')
        except Exception as error:
            QMessageBox.warning(self, 'No se pudo leer la fuente CICA', str(error))
        finally:
            self.setEnabled(True)

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
        self.update_predio_summary()
        self.status.setText(f'{key}: preparado temporalmente. Use «Usar fuente de datos» para aplicarlo.')

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
        self.update_predio_summary()
        self.status.setText('Geodatabase preparada. Pulse «Usar fuente de datos» para aplicarla. Si una tabla también tiene CSV seleccionado, se utiliza el CSV.')

    def validate_inputs(self):
        if self.source_mode.currentIndex() == 1 and not self.replace_references:
            QMessageBox.warning(self, 'Fuente pendiente', 'Pulse «Leer tablas» antes de usar esta fuente.')
            return
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
