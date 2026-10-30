"""Prepare independent CICA CSV snapshots for temporary validation tables."""
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QHeaderView, QComboBox, QDialog, QFileDialog, QTreeWidget, QTreeWidgetItem, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)
from .cica_data import TABLES as CSV_INPUTS, prepare_csv, prepare_repository_cica, predio_status_summary, read_repository_cica_date, read_repository_cica_options, cica_selection
from .cica_gdb import prepare_gdb, UnidentifiedGdbCrs
from .current_references import municipal_names
from pathlib import Path


class CicaIngestionDialog(QDialog):
    copyReadProgress = pyqtSignal(str)

    def __init__(self, parent=None, references=None, geodatabase=None, allow_gdb=True):
        super().__init__(parent)
        self.setWindowTitle('Seleccionar fuente de datos CICA')
        self.replace_references = False
        self.resize(900, 800)
        self.setMinimumSize(650, 540)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setObjectName('cicaSourceDialog')
        self.setStyleSheet("""
            QDialog#cicaSourceDialog { background: #F3F6FA; }
            QDialog#cicaSourceDialog QWidget { font-size: 13px; color: #17324D; }
            QDialog#cicaSourceDialog QLabel { background: transparent; }
            QDialog#cicaSourceDialog QWidget[card="true"] { background: white; border: 1px solid #E2EAF2; border-radius: 10px; }
            QDialog#cicaSourceDialog QLabel[sectionTitle="true"] { font-weight: bold; font-size: 15px; color: #0066B3; }
            QDialog#cicaSourceDialog QLabel[muted="true"] { color: #60758A; font-size: 12px; }
            QDialog#cicaSourceDialog QComboBox, QDialog#cicaSourceDialog QLineEdit { background: #F8FBFE; color: #17324D; border: 1px solid #CBDCEA; border-radius: 5px; padding: 6px; min-height: 20px; }
            QDialog#cicaSourceDialog QPushButton { background: white; color: #0066B3; border: 1px solid #BCD2E4; border-radius: 6px; padding: 7px 13px; font-weight: bold; min-height: 19px; }
            QDialog#cicaSourceDialog QPushButton:hover { background: #EAF2FA; border-color: #0066B3; }
            QDialog#cicaSourceDialog QPushButton[primary="true"] { background: #0066B3; color: white; border-color: #0066B3; }
            QDialog#cicaSourceDialog QPushButton[primary="true"]:hover { background: #005493; }
            QDialog#cicaSourceDialog QPushButton[readAction="true"] { background: #217346; color: white; border-color: #217346; }
            QDialog#cicaSourceDialog QPushButton:disabled { color: #899BAB; background: #EEF2F6; border-color: #DCE5ED; }
            QDialog#cicaSourceDialog QTreeWidget { background: white; alternate-background-color: #F3F8FC; color: #17324D; border: 1px solid #DCE6EF; border-radius: 5px; }
            QDialog#cicaSourceDialog QTreeWidget::item { padding: 5px; min-height: 21px; }
            QDialog#cicaSourceDialog QTreeWidget::item:selected { background: #DBEBF9; color: #17324D; }
            QDialog#cicaSourceDialog QHeaderView::section { background: #EAF2FA; color: #0066B3; border: none; padding: 7px; font-weight: bold; }
            QDialog#cicaSourceDialog QScrollArea { background: transparent; border: none; }
            QDialog#cicaSourceDialog QWidget#sourceContent { background: #F3F6FA; }
        """)
        self.prepared = {}
        self.prepared_gdb = None
        self.allow_gdb = allow_gdb
        self.existing_gdb = geodatabase if allow_gdb else None
        self.existing = dict(references or {})
        self.files = {}
        self.summary_cache = {}
        self.repository_options = []
        self.municipality_catalog = municipal_names(Path(__file__).parent / "resources" / "data" / "divipola.xlsx")
        self.loaded_selection = None
        outer = QVBoxLayout(self); outer.setContentsMargins(18, 16, 18, 14); outer.setSpacing(10)
        title = QLabel('Seleccione la base CICA a validar')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #0066B3;')
        outer.addWidget(title)
        subtitle = QLabel('Defina el origen, el municipio y las etapas antes de usar los datos.')
        subtitle.setProperty('muted', True); subtitle.setWordWrap(True); outer.addWidget(subtitle)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget(); content.setObjectName('sourceContent')
        layout = QVBoxLayout(content); layout.setContentsMargins(0, 0, 4, 0); layout.setSpacing(12)
        scroll.setWidget(content); outer.addWidget(scroll, 1)

        def card(title):
            widget = QWidget(); widget.setProperty('card', True)
            body = QVBoxLayout(widget); body.setContentsMargins(15, 12, 15, 12); body.setSpacing(9)
            heading = QLabel(title); heading.setProperty('sectionTitle', True); body.addWidget(heading)
            layout.addWidget(widget)
            return widget, body

        _, source_layout = card('1. Fuente de datos')
        self.source_mode = QComboBox()
        self.source_mode.addItems(['Archivos CSV del usuario', 'Copia base CICA'])
        source_layout.addWidget(self.source_mode)
        self.repository_date = QLabel(); self.repository_date.setWordWrap(True)
        self.repository_date.setStyleSheet('QLabel { background: #EAF2FA; color: #0066B3; padding: 9px; border-radius: 5px; }')
        self.repository_date.hide(); source_layout.addWidget(self.repository_date)
        self.source_note = QLabel('Cargue los CSV y, si corresponde, una GDB. Los originales no se modifican.')
        self.source_note.setProperty('muted', True); self.source_note.setWordWrap(True); source_layout.addWidget(self.source_note)

        self.copy_filters, filter_layout = card('2. Municipio y etapas')
        municipality_row = QHBoxLayout()
        municipality_row.addWidget(QLabel('Municipio · DIVIPOLA'))
        municipality_row.addStretch()
        self.load_options_button = QPushButton('Consultar municipios y etapas')
        self.load_options_button.clicked.connect(self.load_source_options)
        municipality_row.addWidget(self.load_options_button); filter_layout.addLayout(municipality_row)
        location_form = QFormLayout(); location_form.setSpacing(8)
        self.department = QComboBox(); self.department.addItem('Todos los departamentos', '')
        self.department.currentIndexChanged.connect(self.populate_municipalities)
        location_form.addRow('Departamento', self.department)
        self.municipality = QComboBox(); self.municipality.addItem('Seleccione municipio por DIVIPOLA…', None)
        location_form.addRow('Municipio', self.municipality)
        filter_layout.addLayout(location_form)
        self.stage_summary = QLabel('Consulte los municipios para ver las etapas disponibles.')
        self.stage_summary.setProperty('muted', True); self.stage_summary.setWordWrap(True)
        filter_layout.addWidget(self.stage_summary)
        self.stages = QTreeWidget(); self.stages.setHeaderLabels(['Etapas a validar', 'Predios'])
        self.stages.setRootIsDecorated(False); self.stages.setAlternatingRowColors(True)
        self.stages.setSelectionMode(QAbstractItemView.NoSelection)
        self.stages.setMinimumHeight(190); self.stages.setMaximumHeight(310)
        self.stages.header().setStretchLastSection(False)
        self.stages.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stages.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        filter_layout.addWidget(self.stages)
        stage_buttons = QHBoxLayout()
        select_stages = QPushButton('Seleccionar todas'); clear_stages = QPushButton('Deseleccionar todas')
        select_stages.clicked.connect(lambda: self.check_stages(True)); clear_stages.clicked.connect(lambda: self.check_stages(False))
        stage_buttons.addWidget(select_stages); stage_buttons.addWidget(clear_stages); stage_buttons.addStretch()
        self.read_repository = QPushButton('Leer copia base CICA')
        self.read_repository.setProperty('readAction', True)
        self.read_repository.clicked.connect(self.choose_repository); stage_buttons.addWidget(self.read_repository)
        filter_layout.addLayout(stage_buttons)
        self.municipality.currentIndexChanged.connect(self.update_stages)
        self.stages.itemChanged.connect(self.source_filter_changed)
        self.copy_filters.hide()

        self.csv_card, csv_layout = card('2. Archivos CSV')
        form = QFormLayout(); form.setSpacing(9); csv_layout.addLayout(form)
        self.csv_buttons = []; self.csv_rows = []
        for label, table in CSV_INPUTS.items():
            field = QLineEdit(); field.setReadOnly(True); field.setPlaceholderText('Sin archivo seleccionado')
            if table in self.existing:
                ref = self.existing[table]; field.setText(f'{ref.filename} · {ref.row_count} registros')
            button = QPushButton('Seleccionar CSV…'); self.csv_buttons.append(button)
            button.clicked.connect(lambda _=False, key=label: self.choose_csv(key))
            row_widget = QWidget(); row = QHBoxLayout(row_widget); row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(field, 1); row.addWidget(button)
            row_label = QLabel(label); form.addRow(row_label, row_widget)
            self.csv_rows.append((row_label, row_widget)); self.files[label] = field

        self.gdb_card, gdb_layout = card('3. Geodatabase CICA')
        self.gdb_card.setVisible(allow_gdb)
        gdb_note = QLabel('Seleccione una carpeta .gdb o un ZIP que contenga una geodatabase.')
        gdb_note.setWordWrap(True); gdb_note.setProperty('muted', True); gdb_layout.addWidget(gdb_note)
        self.gdb = QLineEdit(); self.gdb.setReadOnly(True); self.gdb.setPlaceholderText('Sin geodatabase seleccionada')
        if self.existing_gdb:
            self.gdb.setText(f'{self.existing_gdb.filename} · {len(self.existing_gdb.layers)} capas/tablas')
        choose_gdb = QPushButton('Seleccionar GDB…'); choose_gdb.clicked.connect(self.choose_gdb)
        gdb_row = QHBoxLayout(); gdb_row.addWidget(self.gdb, 1); gdb_row.addWidget(choose_gdb); gdb_layout.addLayout(gdb_row)

        _, summary_layout = card('Resumen de la base seleccionada')
        self.predio_summary = QLabel(); self.predio_summary.setWordWrap(True)
        self.predio_summary.setStyleSheet('QLabel { background: #F0F7F3; color: #217346; padding: 10px; border-radius: 6px; }')
        summary_layout.addWidget(self.predio_summary)
        layout.addStretch()
        self.status = QLabel('Seleccione los datos que usará en esta validación.')
        self.status.setProperty('muted', True); self.status.setWordWrap(True); outer.addWidget(self.status)
        self.copyReadProgress.connect(self.status.setText)
        buttons = QHBoxLayout()
        temporary = QLabel('Uso temporal · Sin cambios en los originales'); temporary.setProperty('muted', True)
        buttons.addWidget(temporary); buttons.addStretch()
        cancel = QPushButton('Cancelar'); cancel.clicked.connect(self.reject)
        apply = QPushButton('Usar fuente de datos'); apply.setProperty('primary', True); apply.clicked.connect(self.validate_inputs)
        buttons.addWidget(cancel); buttons.addWidget(apply); outer.addLayout(buttons)
        self.source_mode.currentIndexChanged.connect(self.change_source_mode)
        if not allow_gdb:
            self.source_note.setText('Cargue los CSV para las validaciones de cargue al SNC. Los originales no se modifican.')
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
        self.csv_card.setVisible(index == 0)
        self.source_note.setText(('Lea la copia del municipio y las etapas que seleccione.' + (' Puede agregar una GDB para validar.' if self.allow_gdb else '')) if index == 1 else ('Cargue los CSV y, si corresponde, una GDB. Los originales no se modifican.' if self.allow_gdb else 'Cargue los CSV para las validaciones de cargue al SNC. Los originales no se modifican.'))
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
        selected = [self.stages.topLevelItem(i) for i in range(self.stages.topLevelItemCount()) if self.stages.topLevelItem(i).checkState(0) == Qt.Checked]
        count = sum(int(item.text(1).replace('.', '')) for item in selected)
        self.stage_summary.setText(f'{len(selected)} de {self.stages.topLevelItemCount()} etapas seleccionadas · {count:,} predios'.replace(',', '.'))
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
            self.department.blockSignals(True)
            self.department.clear(); self.department.addItem('Todos los departamentos', '')
            departments = {code[:2] for code, stage, count in options if code and len(code) == 5 and code.isdigit()}
            def department_name(prefix):
                return next((self.municipality_catalog[code][0] for code, stage, count in options if code.startswith(prefix) and code in self.municipality_catalog), 'Departamento sin nombre en catálogo')
            for prefix in sorted(departments, key=lambda prefix: (department_name(prefix), prefix)):
                self.department.addItem(f'{department_name(prefix)} · {prefix}', prefix)
            self.department.blockSignals(False)
            self.populate_municipalities()
            self.status.setText('Seleccione un municipio o Todos y marque las etapas a validar. Después pulse «Leer copia base CICA».')
        except Exception as error:
            QMessageBox.warning(self, 'No se pudieron consultar municipios y etapas', str(error))
        finally:
            self.setEnabled(True)

    def populate_municipalities(self, *_):
        department = self.department.currentData() or ''
        municipalities = {code for code, stage, count in self.repository_options if code and len(code) == 5 and code.isdigit() and (not department or code.startswith(department))}
        totals = {}
        for code, stage, count in self.repository_options:
            totals[code] = totals.get(code, 0) + count
        self.municipality.blockSignals(True)
        self.municipality.clear()
        self.municipality.addItem('Seleccione municipio por DIVIPOLA…', None)
        if not department:
            self.municipality.addItem('Todos los municipios', '')
        for code in sorted(municipalities, key=lambda code: (*self.municipality_catalog.get(code, ('', 'Municipio sin nombre en catálogo')), code)):
            dep_name, name = self.municipality_catalog.get(code, ('Departamento sin nombre', 'Municipio sin nombre en catálogo'))
            label = f'{name} · {code} · {totals[code]:,} predios'.replace(',', '.')
            if not department:
                label = dep_name + ' / ' + label
            self.municipality.addItem(label, code)
        self.municipality.blockSignals(False)
        self.update_stages()

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
            item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
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
            prepared = owner.report_task(prepare_repository_cica, params, selection['municipality'], selection['stages'], progress=self.copyReadProgress.emit)
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
        if not self.allow_gdb:
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Seleccione una geodatabase comprimida', '', 'Geodatabase comprimida (*.zip)')
        if not path:
            path = QFileDialog.getExistingDirectory(self, 'Seleccione la carpeta .gdb')
        if not path:
            return
        self.setEnabled(False)
        self.status.setText('Preparando geodatabase temporal…')
        try:
            owner = self.parent()
            overrides = {}
            while True:
                try:
                    prepared = owner.report_task(prepare_gdb, path, crs_overrides=overrides) if owner is not None and hasattr(owner, 'report_task') else prepare_gdb(path, crs_overrides=overrides)
                    break
                except UnidentifiedGdbCrs as unresolved:
                    overrides[unresolved.layer_name] = 9377
                    if unresolved.wkt:
                        overrides[('wkt', unresolved.wkt)] = 9377
        except Exception as error:
            QMessageBox.warning(self, 'No se cargó la geodatabase', str(error))
            return
        finally:
            self.setEnabled(True)
        if self.prepared_gdb:
            self.prepared_gdb.close()
        self.prepared_gdb = prepared
        self.gdb.setText(f'{prepared.filename} · {len(prepared.layers)} capas/tablas')
        self.gdb.setToolTip('\n'.join(f'{layer.source_name} → {name}: {layer.row_count} registros' + (f' · EPSG:{layer.srid}' if layer.srid else '') for name, layer in prepared.layers.items()))
        self.update_predio_summary()
        self.status.setText('Geodatabase preparada. Pulse «Usar fuente de datos» para aplicarla. Si una tabla también tiene CSV seleccionado, se utiliza el CSV.')

    def validate_inputs(self):
        if self.source_mode.currentIndex() == 1 and (not self.replace_references or self.loaded_selection != self.selected_source_filter()):
            QMessageBox.warning(self, 'Fuente pendiente', 'Pulse «Leer tablas» antes de usar esta fuente.')
            return
        if not (self.prepared or self.existing or self.prepared_gdb or self.existing_gdb):
            QMessageBox.warning(self, 'Sin insumos', 'Seleccione al menos un CSV o una geodatabase.' if self.allow_gdb else 'Seleccione al menos un CSV o lea la Copia base CICA.')
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
