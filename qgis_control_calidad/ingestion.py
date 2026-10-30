"""Prepare independent CICA CSV snapshots for temporary validation tables."""
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QTreeWidget, QTreeWidgetItem, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)
from .cica_data import TABLES as CSV_INPUTS, prepare_csv, prepare_repository_cica, predio_status_summary, read_repository_cica_date, read_repository_cica_options, cica_selection
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
        self.repository_options = []
        self.loaded_selection = None
        layout = QVBoxLayout(self)
        note = QLabel('Seleccione los CSV individualmente y la geodatabase (.gdb o .zip). Los archivos se usarán temporalmente durante la validación, sin modificar los originales. Puede reemplazar un archivo sin volver a seleccionar los demás.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.source_mode = QComboBox()
        self.source_mode.addItems(['Archivos CSV del usuario', 'Copia base CICA'])
        layout.addWidget(self.source_mode)
        self.repository_date = QLabel()
        self.repository_date.setWordWrap(True)
        self.repository_date.setStyleSheet('QLabel { background: #EAF2FA; color: #0066B3; padding: 8px; border-radius: 5px; }')
        self.repository_date.hide()
        layout.addWidget(self.repository_date)
        self.copy_filters = QWidget()
        filter_layout = QVBoxLayout(self.copy_filters)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        self.load_options_button = QPushButton('Consultar municipios y etapas')
        self.load_options_button.clicked.connect(self.load_source_options)
        filter_layout.addWidget(self.load_options_button)
        self.municipality = QComboBox()
        self.municipality.addItem('Seleccione municipio por DIVIPOLA…', None)
        filter_layout.addWidget(self.municipality)
        self.stages = QTreeWidget()
        self.stages.setHeaderLabels(['Etapas a validar', 'Predios'])
        self.stages.setRootIsDecorated(False)
        self.stages.setMinimumHeight(115)
        filter_layout.addWidget(self.stages)
        stage_buttons = QHBoxLayout()
        select_stages = QPushButton('Seleccionar todas'); clear_stages = QPushButton('Deseleccionar todas')
        select_stages.clicked.connect(lambda: self.check_stages(True))
        clear_stages.clicked.connect(lambda: self.check_stages(False))
        stage_buttons.addWidget(select_stages); stage_buttons.addWidget(clear_stages)
        filter_layout.addLayout(stage_buttons)
        self.municipality.currentIndexChanged.connect(self.update_stages)
        self.stages.itemChanged.connect(self.source_filter_changed)
        self.copy_filters.hide()
        layout.addWidget(self.copy_filters)
        self.read_repository = QPushButton('Leer copia base CICA')
        self.read_repository.clicked.connect(self.choose_repository)
        self.read_repository.setVisible(False)
        layout.addWidget(self.read_repository)
        self.source_mode.currentIndexChanged.connect(self.change_source_mode)
        self.csv_buttons = []
        self.csv_rows = []
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
            row_widget = QWidget()
            row = QHBoxLayout(row_widget); row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(field, 1); row.addWidget(button)
            row_label = QLabel(label)
            form.addRow(row_label, row_widget)
            self.csv_rows.append((row_label, row_widget))
            self.files[label] = field
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
            self.predio_summary.setText(source + '\n' + text + ('\nTotales de la copia leída con el municipio y etapas seleccionados.' if repository else '\nTotales generales, sin filtros.') + ' Conteo de registros de cica_predio.')
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
        self.copy_filters.setVisible(index == 1)
        self.repository_date.setVisible(index == 1)
        for label, row in self.csv_rows:
            label.setVisible(index == 0)
            row.setVisible(index == 0)
        for button in self.csv_buttons:
            button.setEnabled(index == 0)
        if index == 1:
            self.refresh_repository_date()
        self.update_predio_summary()

    def refresh_repository_date(self, params=None):
        self.repository_date.setText('Consultando fecha de marca de la copia espejo…')
        owner = self.parent()
        if owner is None or not hasattr(owner, 'repository_connection_params'):
            self.repository_date.setText('Copia base CICA — Fecha y hora no disponibles. Requiere conexión a sentencias.')
            return
        params = params or owner.repository_connection_params()
        if not params:
            self.repository_date.setText('Copia base CICA — Fecha y hora no disponibles. Falta acceso a sentencias.')
            return
        self.setEnabled(False)
        try:
            value = owner.report_task(read_repository_cica_date, params)
            if value is None:
                message = 'Copia base CICA — Fecha y hora sin registrar.'
            else:
                date = value.strftime('%d/%m/%Y · %H:%M:%S %Z').strip() if hasattr(value, 'hour') else value.strftime('%d/%m/%Y') if hasattr(value, 'strftime') else str(value)
                message = 'Copia base CICA — ' + date
            self.repository_date.setText(message)
            self.repository_date.setToolTip('Origen: sentencias.snc_cica_crudo._control')
        except Exception as error:
            self.repository_date.setText('Copia base CICA — Fecha y hora no disponibles: ' + str(error))
        finally:
            self.setEnabled(True)

    def source_filter_changed(self, *_):
        if self.loaded_selection is not None and self.selected_source_filter() != self.loaded_selection:
            self.status.setText('Cambió el municipio o las etapas. Pulse «Leer copia base CICA» para actualizar los datos.')
            self.predio_summary.setText('Resumen pendiente de actualizar con los nuevos filtros.')

    def selected_source_filter(self):
        return cica_selection(self.municipality.currentData() or '',
            [self.stages.topLevelItem(i).data(0, Qt.UserRole) for i in range(self.stages.topLevelItemCount())
             if self.stages.topLevelItem(i).checkState(0) == Qt.Checked])

    def check_stages(self, checked):
        for i in range(self.stages.topLevelItemCount()):
            self.stages.topLevelItem(i).setCheckState(0, Qt.Checked if checked else Qt.Unchecked)

    def load_source_options(self):
        owner = self.parent()
        if owner is None:
            return
        params = owner.repository_connection_params()
        if not params:
            return
        self.setEnabled(False)
        try:
            options = owner.report_task(read_repository_cica_options, params)
            self.repository_options = options
            self.municipality.blockSignals(True)
            self.municipality.clear()
            self.municipality.addItem('Seleccione municipio por DIVIPOLA…', None)
            self.municipality.addItem('Todos los municipios', '')
            municipalities = sorted({code for code, stage, count in options if code and len(code) == 5 and code.isdigit()})
            for code in municipalities:
                count = sum(count for municipality, stage, count in options if municipality == code)
                self.municipality.addItem(f'{code} · {count:,} predios'.replace(',', '.'), code)
            self.municipality.blockSignals(False)
            self.update_stages()
            self.status.setText('Seleccione un municipio o Todos y marque las etapas a validar. Después pulse «Leer copia base CICA».')
        except Exception as error:
            QMessageBox.warning(self, 'No se pudieron consultar municipios y etapas', str(error))
        finally:
            self.setEnabled(True)

    def update_stages(self, *_):
        self.stages.blockSignals(True)
        self.stages.clear()
        municipality = self.municipality.currentData()
        totals = {}
        if municipality is not None:
            for code, stage, count in self.repository_options:
                if not municipality or code == municipality:
                    totals[stage] = totals.get(stage, 0) + count
        for stage, count in sorted(totals.items()):
            item = QTreeWidgetItem([stage or 'Sin etapa', f'{count:,}'.replace(',', '.')])
            item.setData(0, Qt.UserRole, stage)
            item.setCheckState(0, Qt.Checked)
            self.stages.addTopLevelItem(item)
        self.stages.blockSignals(False)
        self.source_filter_changed()

    def choose_repository(self):
        if self.municipality.currentData() is None:
            QMessageBox.warning(self, 'Seleccione municipio', 'Consulte los municipios y etapas y seleccione un DIVIPOLA o Todos los municipios.')
            return
        selection = self.selected_source_filter()
        if not selection['stages']:
            QMessageBox.warning(self, 'Seleccione etapas', 'Marque al menos una etapa para validar.')
            return
        owner = self.parent()
        params = owner.repository_connection_params()
        if not params:
            return
        self.setEnabled(False)
        self.status.setText('Leyendo las siete tablas de sentencias.snc_cica_copy…')
        try:
            prepared = owner.report_task(prepare_repository_cica, params, selection['municipality'], selection['stages'])
            for reference in self.prepared.values():
                reference.close()
            self.prepared = prepared
            self.replace_references = True
            self.loaded_selection = selection
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
        if self.source_mode.currentIndex() == 1 and (not self.replace_references or self.loaded_selection != self.selected_source_filter()):
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
