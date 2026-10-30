"""Read-only CICA progress explorer; its selectors never alter validation filters."""
from collections import defaultdict

from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import (QButtonGroup, QComboBox, QDialog, QDialogButtonBox,
    QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton,
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
        self.resize(1120, 820)
        self.loader = loader
        self.rows = []
        self.reading = False
        self.zone = ''
        self.setStyleSheet('QDialog { background: #F3F6FA; } QLabel { color: #17324D; } QPushButton { padding: 7px 12px; } QTreeWidget { background: white; alternate-background-color: #F3F8FC; } QHeaderView::section { background: #EAF2FA; color: #0066B3; padding: 8px; border: none; font-weight: bold; }')
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 16, 18, 14); layout.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel('Seguimiento CICA por etapas'); title.setStyleSheet(f'font-size: 23px; font-weight: bold; color: {BLUE};')
        header.addWidget(title); header.addStretch()
        self.refresh_button = QPushButton('Actualizar'); self.refresh_button.clicked.connect(self.load)
        header.addWidget(self.refresh_button); layout.addLayout(header)
        self.context = QLabel('Municipio de la fuente: pendiente de consultar.'); self.context.setWordWrap(True)
        layout.addWidget(self.context)
        self.origin = QLabel(); self.origin.setWordWrap(True); self.origin.setTextFormat(Qt.PlainText)
        self.origin.setStyleSheet('color: #60758A; font-size: 11px;'); layout.addWidget(self.origin)
        cards = QHBoxLayout(); self.values = {}
        for key, caption, color in [('total', 'TOTAL PREDIOS', BLUE), ('active', 'ACTIVOS', GREEN), ('cancelled', 'CANCELADOS', RED), ('other', 'OTROS / SIN ESTADO', '#60758A')]:
            card = QFrame(); card.setStyleSheet(f'QFrame {{ background: white; border-left: 4px solid {color}; border-radius: 8px; }} QLabel {{ border: none; }}')
            body = QVBoxLayout(card); body.setContentsMargins(14, 10, 14, 10)
            label = QLabel(caption); label.setStyleSheet(f'color: {color}; font-weight: bold; font-size: 11px;')
            value = QLabel('—'); value.setStyleSheet(f'color: {color}; font-weight: bold; font-size: 28px;')
            body.addWidget(label); body.addWidget(value); self.values[key] = value; cards.addWidget(card)
        layout.addLayout(cards)
        controls = QHBoxLayout(); self.zone_buttons = {}; self.zone_group = QButtonGroup(self)
        self.zone_group.setExclusive(True)
        for zone, label in [('', 'Todas las zonas'), ('Urbano', 'Urbano'), ('Centro poblado', 'Centro poblado'), ('Rural', 'Rural')]:
            button = QPushButton(label); button.setCheckable(True); button.setChecked(not zone)
            button.setStyleSheet(f'QPushButton {{ background: white; color: {BLUE}; border: 1px solid #CCDDEB; border-radius: 6px; }} QPushButton:checked {{ background: {BLUE}; color: white; }}')
            button.clicked.connect(lambda _checked, value=zone: self.set_zone(value))
            self.zone_group.addButton(button); self.zone_buttons[zone] = button; controls.addWidget(button)
        controls.addStretch()
        self.mode = QComboBox(); self.mode.addItems(['Cantidad', 'Porcentaje']); self.mode.currentIndexChanged.connect(self.render)
        controls.addWidget(self.mode); layout.addLayout(controls)
        cp_row = QHBoxLayout(); self.cp_label = QLabel('Códigos CP · NPN posiciones 6–7')
        self.cp = QComboBox(); self.cp.currentIndexChanged.connect(self.render)
        cp_row.addWidget(self.cp_label); cp_row.addWidget(self.cp, 1)
        layout.addLayout(cp_row); self.cp_label.hide(); self.cp.hide()
        self.tabs = QTabWidget(); layout.addWidget(self.tabs, 1)
        self.chart_scroll = QScrollArea(); self.chart_scroll.setWidgetResizable(True); self.chart_scroll.setFrameShape(QScrollArea.NoFrame)
        self.chart_content = QWidget(); self.chart_content.setStyleSheet('background: white;'); self.chart_layout = QGridLayout(self.chart_content)
        self.chart_layout.setColumnStretch(1, 1); self.chart_layout.setColumnStretch(3, 1)
        self.chart_scroll.setWidget(self.chart_content); self.tabs.addTab(self.chart_scroll, 'Avance por etapa')
        self.table = QTreeWidget(); self.table.setRootIsDecorated(False); self.table.setAlternatingRowColors(True)
        self.table.setHeaderLabels(['DIVIPOLA', 'Zona', 'Código zona (6–7)', 'Etapa', 'Total', 'Activos', 'Cancelados', 'Otros estados'])
        self.tabs.addTab(self.table, 'Detalle por zona')
        self.note = QLabel('Las opciones de este informe solo cambian la visualización. El alcance de validación conserva sus filtros.'); self.note.setWordWrap(True)
        self.note.setStyleSheet('color: #60758A; font-size: 11px;'); layout.addWidget(self.note)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Close); self.buttons.button(QDialogButtonBox.Close).setText('Cerrar'); self.buttons.rejected.connect(self.reject); layout.addWidget(self.buttons)
        QTimer.singleShot(0, self.load)

    def set_data(self, data):
        self.rows = list(data.get('rows', []))
        self.context.setText('Municipio de la fuente: ' + data.get('municipality_label', 'Municipios de la fuente seleccionada'))
        self.origin.setText(data.get('source', '') + (' · Actualización: ' + str(data['date']) if data.get('date') else ''))
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
        self.cp_label.setVisible(zone == 'Centro poblado'); self.cp.setVisible(zone == 'Centro poblado')
        self.render()

    def render(self, *_):
        code = self.cp.currentData() or ''
        rows = [row for row in self.rows if (not self.zone or row[1] == self.zone) and
                (self.zone != 'Centro poblado' or not code or row[2] == code)]
        totals = [sum(row[index] for row in rows) for index in range(4, 8)]
        for key, value in zip(('total', 'active', 'cancelled', 'other'), totals): self.values[key].setText(number(value))
        self.table.clear()
        for row in rows:
            item = QTreeWidgetItem([str(value) if index < 4 else number(value) for index, value in enumerate(row)])
            if not row[3]: item.setText(3, 'Sin etapa')
            from qgis.PyQt.QtGui import QColor
            item.setForeground(5, QColor(GREEN)); item.setForeground(6, QColor(RED))
            for index in range(4, 8): item.setTextAlignment(index, Qt.AlignRight | Qt.AlignVCenter)
            self.table.addTopLevelItem(item)
        for index in range(8): self.table.resizeColumnToContents(index)
        while self.chart_layout.count():
            item = self.chart_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.chart_layout.addWidget(QLabel('Etapa registrada'), 0, 0)
        for column, label, color in [(1, 'Activos', GREEN), (3, 'Cancelados', RED)]:
            heading = QLabel(label); heading.setStyleSheet(f'font-weight: bold; color: {color};'); self.chart_layout.addWidget(heading, 0, column, 1, 2)
        stages = defaultdict(lambda: [0, 0])
        for row in rows:
            stages[row[3]][0] += row[5]; stages[row[3]][1] += row[6]
        if not rows:
            self.chart_layout.addWidget(QLabel('No hay predios para esta selección.'), 1, 0, 1, 5)
        for index, (stage, counts) in enumerate(sorted(stages.items()), 1):
            label = QLabel((stage or 'Sin etapa').replace('_', ' ').capitalize()); label.setWordWrap(True); label.setToolTip(stage)
            self.chart_layout.addWidget(label, index, 0)
            for position, (count, total, color) in enumerate(zip(counts, totals[1:3], (GREEN, RED))):
                percent = 100 * count / total if total else 0
                denominator = total if self.mode.currentText() == 'Porcentaje' else max(totals[1:3], default=0)
                bar = QProgressBar(); bar.setRange(0, 1000); bar.setValue(round(1000 * count / denominator) if denominator else 0); bar.setTextVisible(False)
                bar.setFixedHeight(18); bar.setStyleSheet(f'QProgressBar {{ background: #EAF0F5; border: none; border-radius: 4px; }} QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}')
                tip = f'{number(count)} de {number(total)} · {percent:.1f} %'; bar.setToolTip(tip)
                value = QLabel(f'{number(count)} | {percent:.1f} %'); value.setStyleSheet(f'color: {color}; font-weight: bold;'); value.setToolTip(tip)
                self.chart_layout.addWidget(bar, index, 1 + position * 2); self.chart_layout.addWidget(value, index, 2 + position * 2)
        self.chart_layout.setRowStretch(len(stages) + 2, 1)
        self.note.setText('Cada porcentaje usa el total del estado (activos o cancelados) en la zona visible. Las etapas se muestran como están registradas. Esta vista no modifica los filtros de validación.')

    def load(self):
        if self.reading: return
        self.reading = True; self.refresh_button.setEnabled(False); self.buttons.setEnabled(False)
        try:
            self.set_data(self.loader())
        except Exception as error:
            self.rows = []; self.render()
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
