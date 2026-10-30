"""Read-only CICA progress explorer; its selectors never alter validation filters."""

from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import (QButtonGroup, QComboBox, QDialog, QDialogButtonBox,
    QFrame, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

GREEN = '#217346'
BLUE = '#0066B3'
RED = '#BE594D'


def number(value):
    return f'{value:,}'.replace(',', '.')


class CicaProgressDialog(QDialog):
    def __init__(self, loader, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Informe de avance CICA')
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.resize(1160, 860)
        self.loader = loader
        self.rows = []
        self.reading = False
        self.zone = ''
        self.data = {}
        self.setStyleSheet("""QDialog { background: #F3F6FA; } QLabel { color: #17324D; font-size: 13px; }
            QPushButton { font-size: 12px; background: white; color: #0066B3; border: 1px solid #D9E5EF; border-radius: 8px; padding: 9px 14px; }
            QPushButton:checked { background: #0066B3; color: white; border-color: #0066B3; }
            QScrollArea { border: none; background: #F3F6FA; }
            QTreeWidget { background: white; alternate-background-color: #F3F8FC; }
            QHeaderView::section { background: #EAF2FA; color: #0066B3; padding: 8px; border: none; font-weight: bold; }
        """)
        outer = QVBoxLayout(self); outer.setContentsMargins(18, 14, 18, 12)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); outer.addWidget(scroll, 1)
        content = QWidget(); content.setObjectName('cicaProgressContent'); content.setStyleSheet('QWidget#cicaProgressContent { background: #F3F6FA; }')
        layout = QVBoxLayout(content); layout.setSpacing(14); layout.setContentsMargins(0, 0, 5, 0); scroll.setWidget(content)
        self.context = QLabel('Municipio de la fuente: pendiente de consultar.'); self.context.setWordWrap(True)
        self.context.setStyleSheet('font-weight: bold; font-size: 14px;'); layout.addWidget(self.context)
        hint = QLabel('Se actualiza con el municipio seleccionado para validar. No requiere seleccionarlo de nuevo.')
        hint.setStyleSheet('color: #60758A; font-size: 11px;'); hint.setWordWrap(True); layout.addWidget(hint)
        header = QHBoxLayout()
        self.origin = QLabel('Actualización de datos: pendiente de consultar.'); self.origin.setWordWrap(True)
        self.origin.setStyleSheet('color: #60758A; font-size: 11px;'); header.addWidget(self.origin, 1)
        for caption, color in [('Reconocimiento', GREEN), ('Control', BLUE), ('Cancelados', RED)]:
            legend = QLabel('■ ' + caption); legend.setStyleSheet(f'color: {color}; font-size: 11px;'); header.addWidget(legend)
        self.refresh_button = QPushButton('Actualizar'); self.refresh_button.clicked.connect(self.load); header.addWidget(self.refresh_button)
        layout.addLayout(header)
        cards = QHBoxLayout(); self.values = {}
        for key, caption, color in [('total', 'TOTAL PREDIOS', BLUE), ('active', 'ACTIVOS', GREEN), ('cancelled', 'CANCELADOS', RED)]:
            card, body = self.card()
            card.setStyleSheet(f'QFrame {{ background: white; border-left: 4px solid {color}; border-radius: 10px; }} QLabel {{ border: none; background: transparent; }}')
            label = QLabel(caption); label.setStyleSheet(f'color: {color}; font-size: 11px;')
            value = QLabel('—'); value.setStyleSheet(f'color: {color}; font-size: 29px; font-weight: bold;')
            body.addWidget(label); body.addWidget(value); self.values[key] = value; cards.addWidget(card, 1)
        layout.addLayout(cards)
        controls = QHBoxLayout(); self.zone_buttons = {}; self.zone_group = QButtonGroup(self); self.zone_group.setExclusive(True)
        for zone, label in [('', 'Todas las zonas'), ('Urbano', 'Urbano'), ('Centro poblado', 'Centro poblado'), ('Rural', 'Rural')]:
            button = QPushButton(label); button.setCheckable(True); button.setChecked(not zone)
            button.clicked.connect(lambda _checked, value=zone: self.set_zone(value))
            self.zone_group.addButton(button); self.zone_buttons[zone] = button; controls.addWidget(button)
        controls.addStretch()
        self.mode = QComboBox(self); self.mode.addItems(['Cantidad', 'Porcentaje']); self.mode.hide(); self.mode.currentIndexChanged.connect(self.sync_mode)
        self.mode_buttons = {}; mode_group = QButtonGroup(self); mode_group.setExclusive(True)
        for caption in ('Cantidad', 'Porcentaje'):
            button = QPushButton(caption); button.setCheckable(True); button.setChecked(caption == 'Cantidad')
            button.clicked.connect(lambda _checked, text=caption: self.mode.setCurrentText(text))
            mode_group.addButton(button); self.mode_buttons[caption] = button; controls.addWidget(button)
        layout.addLayout(controls)
        self.cp_label = QLabel('Códigos CP encontrados · NPN posiciones 6–7:')
        self.cp = QComboBox(self); self.cp.hide(); self.cp.currentIndexChanged.connect(self.render)
        self.cp_container = QWidget(); self.cp_layout = QHBoxLayout(self.cp_container); self.cp_layout.setContentsMargins(0, 0, 0, 0)
        self.cp_layout.addWidget(self.cp_label)
        self.cp_chips = QWidget(); self.cp_chip_layout = QHBoxLayout(self.cp_chips); self.cp_chip_layout.setContentsMargins(0, 0, 0, 0)
        chip_scroll = QScrollArea(); chip_scroll.setFrameShape(QScrollArea.NoFrame); chip_scroll.setWidgetResizable(True); chip_scroll.setWidget(self.cp_chips); chip_scroll.setFixedHeight(46)
        chip_scroll.viewport().setObjectName('cicaCpViewport'); chip_scroll.viewport().setStyleSheet('QWidget#cicaCpViewport { background: #F3F6FA; }')
        self.cp_chips.setObjectName('cicaCpChips'); self.cp_chips.setStyleSheet('QWidget#cicaCpChips { background: #F3F6FA; }')
        self.cp_layout.addWidget(chip_scroll, 1); layout.addWidget(self.cp_container); self.cp_container.hide()
        self.metric_widgets = {}
        panels = QHBoxLayout()
        for key, title, color in [('recognition', 'Reconocimiento predial', GREEN), ('quality', 'Control de calidad', BLUE)]:
            card, body = self.card(title)
            metrics = []
            for role, caption, role_color in [('active', 'Activos', color), ('cancelled', 'Cancelados', RED)]:
                body.addWidget(QLabel(caption))
                row = QHBoxLayout(); bar = QProgressBar(); bar.setRange(0, 1000); bar.setTextVisible(False); bar.setFixedHeight(20)
                bar.setStyleSheet(f'QProgressBar {{ background: #EAF0F5; border: none; border-radius: 5px; }} QProgressBar::chunk {{ background: {role_color}; border-radius: 5px; }}')
                value = QLabel('—'); value.setStyleSheet(f'color: {role_color}; font-weight: bold;')
                row.addWidget(bar, 1); row.addWidget(value); body.addLayout(row); body.addSpacing(13)
                metrics.append((bar, value, role))
            note = QLabel('Porcentaje sobre el total del estado en la zona seleccionada.'); note.setStyleSheet('color: #60758A; font-size: 10px;'); note.setWordWrap(True); body.addWidget(note)
            self.metric_widgets[key] = metrics; panels.addWidget(card, 1)
        layout.addLayout(panels)
        lower = QHBoxLayout()
        card, body = self.card('Activos sin áreas geográficas')
        row = QHBoxLayout(); self.no_areas = QLabel('—'); self.no_areas.setStyleSheet('color: #D69322; font-size: 28px; font-weight: bold;')
        self.no_areas_percent = QLabel(); row.addWidget(self.no_areas); row.addWidget(self.no_areas_percent)
        self.area_bar = QProgressBar(); self.area_bar.setRange(0, 1000); self.area_bar.setTextVisible(False); self.area_bar.setFixedHeight(18)
        self.area_bar.setStyleSheet('QProgressBar { background: #EAF0F5; border: none; border-radius: 4px; } QProgressBar::chunk { background: #D69322; border-radius: 4px; }')
        row.addWidget(self.area_bar, 1); body.addLayout(row)
        formula = QLabel('Total predios − cancelados − con_areas_geo'); formula.setStyleSheet('color: #60758A; font-size: 10px;'); body.addWidget(formula)
        lower.addWidget(card, 2)
        card, body = self.card('Consultar el detalle')
        detail = QPushButton('Ver tabla y códigos NPN'); detail.setStyleSheet('background: #0066B3; color: white;'); detail.clicked.connect(self.open_detail); body.addWidget(detail)
        note = QLabel('Valores exactos de la zona visible.'); note.setStyleSheet('color: #60758A; font-size: 10px;'); body.addWidget(note); lower.addWidget(card, 1)
        layout.addLayout(lower)
        card, body = self.card()
        card.setStyleSheet('QFrame { background: white; border-left: 5px solid #0096A8; border-radius: 10px; } QLabel { border: none; background: transparent; }')
        title = QLabel('RESULTADO FINAL · CARGADOS A SNC'); title.setStyleSheet('color: #0096A8; font-weight: bold; font-size: 11px;'); body.addWidget(title)
        row = QHBoxLayout(); self.snc = QLabel('—'); self.snc.setStyleSheet('color: #0096A8; font-size: 29px; font-weight: bold;'); row.addWidget(self.snc)
        row.addWidget(QLabel('predios cargados al SNC')); row.addStretch(); self.final_scope = QLabel(); self.final_scope.setWordWrap(True); row.addWidget(self.final_scope); body.addLayout(row); layout.addWidget(card)
        self.note = QLabel(); self.note.setWordWrap(True); self.note.setStyleSheet('color: #60758A; font-size: 11px;'); self.note.hide()
        self.table = QTreeWidget(self); self.table.hide(); self.table.setRootIsDecorated(False); self.table.setAlternatingRowColors(True)
        self.table.setHeaderLabels(['DIVIPOLA', 'Zona', 'Código zona (6–7)', 'Etapa', 'Total', 'Activos', 'Cancelados', 'Otros estados'])
        self.buttons = QDialogButtonBox(QDialogButtonBox.Close); self.buttons.button(QDialogButtonBox.Close).setText('Cerrar'); self.buttons.rejected.connect(self.reject); outer.addWidget(self.buttons)
        QTimer.singleShot(0, self.load)

    def card(self, title=None):
        card = QFrame(); card.setStyleSheet('QFrame { background: white; border-radius: 10px; } QLabel { background: transparent; }')
        body = QVBoxLayout(card); body.setContentsMargins(18, 15, 18, 15); body.setSpacing(9)
        if title:
            heading = QLabel(title); heading.setStyleSheet('font-size: 17px; font-weight: bold;'); body.addWidget(heading)
        return card, body

    def sync_mode(self, *_):
        self.mode_buttons[self.mode.currentText()].setChecked(True)
        self.render()

    def set_data(self, data):
        self.data = data
        self.rows = list(data.get('rows', []))
        self.context.setText('Municipio de la fuente: ' + data.get('municipality_label', 'Municipios de la fuente seleccionada'))
        self.origin.setText('Actualización de datos: ' + str(data.get('date') or 'fecha no disponible'))
        self.origin.setToolTip(data.get('source', ''))
        self.set_zone(self.zone)

    def set_zone(self, zone):
        self.zone = zone
        self.zone_buttons[zone].setChecked(True)
        self.cp.blockSignals(True); previous = self.cp.currentData()
        self.cp.clear(); self.cp.addItem('Todos los CP', '')
        for code in sorted({row[2] for row in self.rows if row[1] == 'Centro poblado'}):
            self.cp.addItem(code, code)
        index = self.cp.findData(previous)
        if index >= 0: self.cp.setCurrentIndex(index)
        self.cp.blockSignals(False)
        self.cp_container.setVisible(zone == 'Centro poblado')
        while self.cp_chip_layout.count():
            item = self.cp_chip_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.cp_buttons = {}
        for index in range(self.cp.count()):
            code = self.cp.itemData(index)
            button = QPushButton('Todos' if not code else code); button.setCheckable(True); button.setChecked(index == self.cp.currentIndex())
            button.clicked.connect(lambda _checked, value=code: self.select_cp(value))
            self.cp_chip_layout.addWidget(button); self.cp_buttons[code] = button
        self.cp_chip_layout.addStretch()
        self.render()

    def select_cp(self, code):
        self.cp.setCurrentIndex(self.cp.findData(code))
        self.render()

    def render(self, *_):
        code = self.cp.currentData() or ''
        rows = [row for row in self.rows if (not self.zone or row[1] == self.zone) and
                (self.zone != 'Centro poblado' or not code or row[2] == code)]
        totals = [sum(row[index] for row in rows) for index in range(4, 8)]
        for key, value in zip(('total', 'active', 'cancelled'), totals[:3]): self.values[key].setText(number(value))
        for value, button in getattr(self, 'cp_buttons', {}).items(): button.setChecked(value == code)
        self.table.clear()
        for row in rows:
            item = QTreeWidgetItem([str(value) if index < 4 else number(value) for index, value in enumerate(row)])
            if not row[3]: item.setText(3, 'Sin etapa')
            from qgis.PyQt.QtGui import QColor
            item.setForeground(5, QColor(GREEN)); item.setForeground(6, QColor(RED))
            for index in range(4, 8): item.setTextAlignment(index, Qt.AlignRight | Qt.AlignVCenter)
            self.table.addTopLevelItem(item)
        for index in range(8): self.table.resizeColumnToContents(index)
        indicators = self.data.get('indicator_rows')
        visible_indicators = [item for item in (indicators or []) if (not self.zone or item['zona'] == self.zone) and (self.zone != 'Centro poblado' or not code or item['codigo_zona'] == code)]
        for key, stages in [('recognition', self.data.get('recognition_stages')),
                            ('quality', self.data.get('quality_stages', ('CONTROL_CALIDAD_GENERAL', 'CONTROL_CALIDAD_GRUPO', 'DEVUELTO', 'RECHAZADO', 'VALIDADO')))]:
            for position, (bar, value, role) in enumerate(self.metric_widgets[key]):
                count = sum(row[5 + position] for row in rows if row[3] in stages) if stages is not None else None
                if indicators is not None:
                    field = ('recognized_' if key == 'recognition' else 'quality_') + ('active' if position == 0 else 'cancelled')
                    count = sum(item[field] for item in visible_indicators)
                denominator = totals[1 + position]
                percent = 100 * count / denominator if count is not None and denominator else 0
                scale = denominator if self.mode.currentText() == 'Porcentaje' else max(totals[1:3], default=0)
                bar.setValue(round(1000 * count / scale) if count is not None and scale else 0)
                value.setText(f'{number(count)} | {percent:.1f} %' if count is not None else '—')
                tip = f'{number(count)} de {number(denominator)} · {percent:.1f} %' if count is not None else 'Pendiente de definir las etapas que corresponden a este indicador.'
                value.setToolTip(tip); bar.setToolTip(tip)
        area_rows = self.data.get('with_areas_rows')
        if indicators is not None and self.data.get('areas_available'):
            area_rows = [(item['divipola'], item['zona'], item['codigo_zona'], item['with_areas']) for item in indicators]
        if area_rows is not None:
            self.no_areas.setToolTip('Total predios − cancelados − predios con área geográfica positiva.')
            with_areas = sum(row[3] for row in area_rows if (not self.zone or row[1] == self.zone) and (self.zone != 'Centro poblado' or not code or row[2] == code))
            missing = totals[0] - totals[2] - with_areas
            if missing < 0:
                self.no_areas.setText('—'); self.no_areas_percent.setText('Datos de áreas por revisar'); self.area_bar.setValue(0)
            else:
                percent = 100 * missing / totals[1] if totals[1] else 0
                self.no_areas.setText(number(missing)); self.no_areas_percent.setText(f'{percent:.1f} % de los activos'); self.area_bar.setValue(round(percent * 10))
        else:
            self.no_areas.setText('—'); self.no_areas_percent.setText(''); self.no_areas.setToolTip('Pendiente de identificar el campo de áreas geográficas.'); self.area_bar.setValue(0)
        snc_stages = self.data.get('snc_stages')
        self.snc.setText(number(sum(row[4] for row in rows if row[3] in snc_stages)) if snc_stages is not None else '—')
        if indicators is not None and self.data.get('snc_available'):
            self.snc.setText(number(sum(item['snc'] for item in visible_indicators)))
        self.snc.setToolTip('VALIDADO y estado_control = DESCARGADO_AL_SNC' if self.data.get('snc_available') else 'El campo estado_control no está disponible en esta fuente.')
        self.final_scope.setText((self.zone or 'Todas las zonas') + (' · ' + (code or 'Todos los códigos CP') if self.zone == 'Centro poblado' else ''))
        self.note.setText('Esta consulta no modifica los filtros de validación.')

    def open_detail(self):
        dialog = QDialog(self); dialog.setWindowTitle('Detalle CICA · ' + (self.zone or 'Todas las zonas')); dialog.resize(1000, 550)
        layout = QVBoxLayout(dialog)
        tabs = QTabWidget(); layout.addWidget(tabs)
        summary = QWidget(); summary_layout = QVBoxLayout(summary)
        self.table.setParent(summary); self.table.show(); summary_layout.addWidget(self.table)
        tabs.addTab(summary, 'Resumen por zona y etapa')
        provider = self.data.get('detail_loader')
        if provider:
            page = QWidget(); body = QVBoxLayout(page)
            codes = QTreeWidget(); codes.setRootIsDecorated(False); codes.setAlternatingRowColors(True)
            codes.setHeaderLabels(['Número Predial Nacional', 'Etapa', 'Estado', 'Registros']); body.addWidget(codes)
            controls = QHBoxLayout(); previous = QPushButton('Anterior'); next_page = QPushButton('Siguiente'); read = QPushButton('Consultar códigos NPN'); status = QLabel('Consulte los códigos de la zona visible.')
            controls.addWidget(read); controls.addWidget(previous); controls.addWidget(next_page); controls.addWidget(status, 1); body.addLayout(controls)
            previous.setEnabled(False); next_page.setEnabled(False)
            state = {'offset': 0}
            def load_page(offset):
                for button in (read, previous, next_page): button.setEnabled(False)
                status.setText('Consultando…')
                try:
                    data = provider(self.zone, self.cp.currentData() or '', offset)
                    codes.clear()
                    for npn, stage, current_state, count in data['rows']:
                        codes.addTopLevelItem(QTreeWidgetItem([npn or '', stage or 'Sin etapa', current_state or 'Sin estado', number(count)]))
                    state['offset'] = offset
                    status.setText(f"Filas {offset + 1}–{offset + len(data['rows'])}" if data['rows'] else 'Sin registros.')
                    for column in range(4): codes.resizeColumnToContents(column)
                    previous.setEnabled(offset > 0); next_page.setEnabled(data.get('has_more', False))
                except Exception as error:
                    codes.clear(); status.setText('No disponible: ' + str(error))
                finally:
                    read.setEnabled(True)
            read.clicked.connect(lambda: load_page(0))
            previous.clicked.connect(lambda: load_page(max(0, state['offset'] - 500)))
            next_page.clicked.connect(lambda: load_page(state['offset'] + 500))
            tabs.addTab(page, 'Códigos NPN')
        buttons = QDialogButtonBox(QDialogButtonBox.Close); buttons.button(QDialogButtonBox.Close).setText('Cerrar'); buttons.rejected.connect(dialog.reject); layout.addWidget(buttons)
        try:
            dialog.exec_()
        finally:
            self.table.hide(); self.table.setParent(self)

    def load(self):
        if self.reading: return
        self.reading = True; self.refresh_button.setEnabled(False); self.buttons.setEnabled(False)
        try:
            self.set_data(self.loader())
        except Exception as error:
            self.rows = []; self.data = {}; self.render()
            for metrics in self.metric_widgets.values():
                for bar, value, role in metrics: bar.setValue(0); value.setText('—')
            self.no_areas.setText('—'); self.snc.setText('—')
            for value in self.values.values(): value.setText('—')
            self.origin.setText('Informe no disponible: ' + str(error))
            QMessageBox.warning(self, 'No se pudo consultar el avance CICA', str(error))
        finally:
            self.reading = False; self.refresh_button.setEnabled(True); self.buttons.setEnabled(True)

    def reject(self):
        if not self.reading: super().reject()

    def closeEvent(self, event):
        if self.reading: event.ignore()
        else: super().closeEvent(event)
