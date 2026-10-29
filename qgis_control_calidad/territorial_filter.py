"""Filter editor and read-only discovery of NPN prefixes from the selected source."""
import csv
import re
from contextlib import closing

import psycopg2
from psycopg2 import sql
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QToolButton, QMenu, QWidgetAction, QWidget, QCheckBox, QTreeWidget, QTreeWidgetItem, QHeaderView, QSizePolicy)
from .territorial_scope import SCOPES, NPN_COLUMNS, normalize_prefixes, scope_members, sector_scope
from .territorial_statistics import included_count, prefix_counts


def prefixes_from_values(values):
    return sorted({str(value).strip()[:17] for value in values
                   if value is not None and re.fullmatch(r'[0-9]{17}', str(value).strip()[:17])})


def read_prefixes(params, schema, model, snapshot=None):
    if snapshot is not None:
        column = next((name for name in NPN_COLUMNS if name in snapshot.columns), None)
        if column is None:
            raise ValueError('La fuente de predios no contiene una columna NPN.')
        index = snapshot.columns.index(column)
        with snapshot.csv_path.open(encoding='utf-8', newline='') as stream:
            return prefixes_from_values(row[index] for row in csv.reader(stream) if len(row) > index)
    if not schema:
        raise ValueError('Seleccione el esquema a validar o cargue la fuente CICA antes de leer los códigos.')
    table = 'cica_predio' if model == 'CICA' else 'ilc_predio'
    options = dict(params); options.setdefault('connect_timeout', 8)
    with closing(psycopg2.connect(**options)) as connection:
        connection.set_session(readonly=True)
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '30s'")
            cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s', (schema, table))
            columns = {row[0] for row in cursor.fetchall()}
            column = next((name for name in NPN_COLUMNS if name in columns), None)
            if not column:
                raise ValueError(f'{table}: no se encontró una columna NPN en la fuente seleccionada.')
            cursor.execute(sql.SQL("SELECT DISTINCT substring(btrim({}::text), 1, 17) FROM {} WHERE substring(btrim({}::text), 1, 17) ~ '^[0-9]{{17}}$' ORDER BY 1").format(
                sql.Identifier(column), sql.Identifier(schema, table), sql.Identifier(column)))
            return [row[0] for row in cursor.fetchall()]


class ScopeSelector(QToolButton):
    """A drop-down checkbox panel that stays open during multiple selections."""
    selectionChanged = pyqtSignal()

    def __init__(self, scope='all', parent=None):
        super().__init__(parent)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.menu = QMenu(self)
        panel = QWidget(self.menu); layout = QVBoxLayout(panel)
        self.checks = {}; self.changing = True
        for key in ('all', 'urban', 'rural', 'center'):
            check = QCheckBox(SCOPES[key], panel)
            self.checks[key] = check; layout.addWidget(check)
            check.toggled.connect(lambda checked, key=key: self.toggle(key, checked))
        action = QWidgetAction(self.menu); action.setDefaultWidget(panel)
        self.menu.addAction(action); self.setMenu(self.menu)
        self.changing = False
        self.set_scope(scope)

    def currentData(self):
        selected = [key for key in ('urban', 'rural', 'center') if self.checks[key].isChecked()]
        return 'all' if len(selected) == 3 else '+'.join(selected) or None

    def set_scope(self, scope):
        members = scope_members(scope)
        self.changing = True
        for key, check in self.checks.items():
            check.setChecked(scope == 'all' if key == 'all' else key in members)
        self.changing = False
        self.update_text()
        self.selectionChanged.emit()

    def toggle(self, key, checked):
        if self.changing:
            return
        self.changing = True
        if key == 'all':
            for name in ('urban', 'rural', 'center'):
                self.checks[name].setChecked(checked)
        else:
            self.checks['all'].setChecked(all(self.checks[name].isChecked() for name in ('urban', 'rural', 'center')))
        self.changing = False
        self.update_text()
        self.selectionChanged.emit()

    def update_text(self):
        self.setText(SCOPES.get(self.currentData(), 'Seleccione ámbito…'))


class TerritorialFilterDialog(QDialog):
    def __init__(self, scope, prefixes, loader, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Filtro avanzado — Modelo Interno / CICA')
        self.resize(800, 700)
        self.loader = loader
        self.statistics = None; self.r1_statistics = None; self.r1_status = 'Pendiente de consultar R1.'; self.counts = {}; self.reading = False
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Datos de la fuente'))
        self.source_label = QLabel('Pendiente de consultar la fuente seleccionada.')
        self.source_label.setWordWrap(True); layout.addWidget(self.source_label)
        cards = QHBoxLayout(); self.stat_labels = {}
        for key, title in (('total', 'Total predios'), ('urban', 'Urbano'), ('rural', 'Rural'), ('center', 'Centro poblado')):
            label = QLabel(title + '\n—')
            label.setStyleSheet('background: #edf6fa; color: #005b80; padding: 10px; border: 1px solid #cbdde6;')
            self.stat_labels[key] = label; cards.addWidget(label)
        layout.addLayout(cards)
        self.stat_note = QLabel('Conteo de registros de predios; incluye duplicados.'); self.stat_note.setWordWrap(True)
        layout.addWidget(self.stat_note)
        self.r1_label = QLabel('R1 — pendiente de consultar.'); self.r1_label.setWordWrap(True)
        self.r1_label.setStyleSheet('background: #f0f7f1; color: #275736; padding: 8px; border: 1px solid #c4ddcc;')
        layout.addWidget(self.r1_label)
        form = QFormLayout(); self.scope = ScopeSelector(scope)
        form.addRow('Ámbito', self.scope); layout.addLayout(form)
        explanation = QLabel('Combine ámbitos. Todos incluye registros sin ámbito identificable. El mismo filtro se aplica a la fuente y a R1/R2; sus cantidades se muestran por separado y no se suman.')
        explanation.setWordWrap(True); layout.addWidget(explanation)
        self.selection_statistics = QLabel('Predios incluidos con este filtro: pendiente de consultar.')
        self.selection_statistics.setStyleSheet('background: #e0f1ff; color: #005b80; padding: 10px; font-weight: bold;')
        self.selection_statistics.setWordWrap(True); layout.addWidget(self.selection_statistics)
        text = QLabel('Manzanas / veredas (opcional): posiciones 1–17 del NPN.\nCódigos presentes en la fuente o en R1. Sin códigos marcados se incluyen todos los del ámbito elegido. El mismo filtro se aplica a la fuente y a R1/R2.')
        text.setWordWrap(True); layout.addWidget(text)
        self.read_button = QPushButton('Actualizar datos de la fuente')
        self.read_button.clicked.connect(self.load_codes); layout.addWidget(self.read_button)
        self.search = QLineEdit(); self.search.setPlaceholderText('Buscar código de 17 dígitos…')
        self.search.textChanged.connect(self.filter_codes); layout.addWidget(self.search)
        selection_buttons = QHBoxLayout()
        self.select_all_button = QPushButton('Seleccionar todo'); self.deselect_all_button = QPushButton('Deseleccionar todo')
        self.select_all_button.clicked.connect(lambda: self.set_visible_checked(True))
        self.deselect_all_button.clicked.connect(lambda: self.set_visible_checked(False))
        for button in (self.select_all_button, self.deselect_all_button):
            button.setToolTip('Actúa sobre los códigos visibles según el ámbito y la búsqueda.')
            selection_buttons.addWidget(button)
        layout.addLayout(selection_buttons)
        self.codes = QTreeWidget(); self.codes.setHeaderLabels(['Código NPN (1–17)', 'Tipo', 'Predios fuente', 'Registros R1'])
        self.codes.setRootIsDecorated(False); self.codes.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for column in (1, 2, 3):
            self.codes.header().setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.codes.setMinimumHeight(140); layout.addWidget(self.codes, 1)
        self.summary = QLabel(); self.summary.setWordWrap(True); layout.addWidget(self.summary)
        self.populate(prefixes, prefixes)
        self.scope.selectionChanged.connect(self.filter_codes)
        self.codes.itemChanged.connect(self.update_summary)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText('Aplicar filtro')
        self.buttons.button(QDialogButtonBox.Cancel).setText('Cancelar')
        self.buttons.accepted.connect(self.accept); self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.update_summary()

    def items(self):
        return (self.codes.topLevelItem(i) for i in range(self.codes.topLevelItemCount()))

    def selected_prefixes(self):
        return normalize_prefixes(item.data(0, Qt.UserRole) for item in self.items() if item.checkState(0) == Qt.Checked)

    def populate(self, codes, selected):
        previous = self.codes.blockSignals(True)
        selected = set(selected)
        r1_counts = prefix_counts(self.r1_statistics) if self.r1_statistics is not None else {}
        try:
            self.codes.clear()
            for code in codes:
                category = sector_scope(code)
                label = {'rural': 'Vereda', 'urban': 'Manzana', 'center': 'Centro poblado'}.get(category, 'Sin ámbito')
                count = str(self.counts.get(code, 0)) if self.statistics is not None else '—'
                r1_count = str(r1_counts.get(code, 0)) if self.r1_statistics is not None else '—'
                item = QTreeWidgetItem([code, label, count, r1_count])
                item.setData(0, Qt.UserRole, code)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Checked if code in selected else Qt.Unchecked)
                self.codes.addTopLevelItem(item)
        finally:
            self.codes.blockSignals(previous)
        self.filter_codes()

    def load_codes(self):
        if self.reading:
            return
        selected = self.selected_prefixes(); self.reading = True
        for widget in (self.read_button, self.buttons, self.scope, self.codes, self.select_all_button, self.deselect_all_button):
            widget.setEnabled(False)
        self.source_label.setText('Leyendo datos de la fuente…')
        try:
            loaded = self.loader()
            if isinstance(loaded, dict) and 'source_statistics' in loaded:
                data = loaded['source_statistics']
                source_error = loaded.get('source_error', '')
                self.r1_statistics = loaded.get('r1_statistics')
                self.r1_status = loaded.get('r1_status', '')
            else:
                data = loaded; source_error = ''
                self.r1_statistics = None; self.r1_status = 'R1 no consultado.'
            if isinstance(data, dict):
                self.statistics = data; self.counts = prefix_counts(data); codes = sorted(self.counts)
                self.source_label.setText('Fuente de validación · ' + data['source'])
                for key, label in self.stat_labels.items():
                    title = {'total': 'Total predios', 'urban': 'Urbano', 'rural': 'Rural', 'center': 'Centro poblado'}[key]
                    value = data['total'] if key == 'total' else data['totals'][key]
                    label.setText(title + '\n' + f'{value:,}'.replace(',', '.'))
                self.stat_note.setText(f"Sin ámbito identificable: {data['totals']['unknown']:,}. Conteo previo a las reglas; incluye registros duplicados.".replace(',', '.'))
            else:
                codes = data or []; self.statistics = None; self.counts = {}
                self.source_label.setText('Fuente no disponible: ' + source_error if source_error else 'Códigos leídos; estadísticas no disponibles.')
                for label in self.stat_labels.values():
                    label.setText(label.text().split('\n')[0] + '\n—')
                self.stat_note.setText('Estadísticas de la fuente no disponibles.')
            if self.r1_statistics is not None:
                r1 = self.r1_statistics; totals = r1['totals']
                counts = f"Total: {r1['total']:,} · Urbano: {totals['urban']:,} · Rural: {totals['rural']:,} · CP: {totals['center']:,} · Sin ámbito: {totals['unknown']:,}".replace(',', '.')
                self.r1_label.setText(r1['source'] + '\n' + counts + '\nConteo de registros R1, incluidos duplicados. No se suma a la fuente de validación.')
            else:
                self.r1_label.setText('R1 — ' + self.r1_status)
            if self.r1_statistics is not None:
                codes = sorted(set(codes) | set(prefix_counts(self.r1_statistics)))
            if set(selected) - set(codes):
                QMessageBox.warning(self, 'Códigos no encontrados', 'Algunos códigos marcados no aparecen en esta fuente. Se conservarán marcados con cero predios; revise la selección.')
            self.populate(sorted(set(codes) | set(selected)), selected)
            self.update_summary()
        except Exception as error:
            self.statistics = None; self.r1_statistics = None; self.counts = {}
            self.r1_status = 'Estadísticas no disponibles.'
            self.r1_label.setText('R1 — ' + self.r1_status)
            self.source_label.setText('No se pudo consultar la fuente. Vuelva a actualizar los datos.')
            for label in self.stat_labels.values():
                label.setText(label.text().split('\n')[0] + '\n—')
            self.stat_note.setText('Estadísticas no disponibles.')
            for item in self.items():
                item.setText(2, '—'); item.setText(3, '—')
            self.update_summary()
            QMessageBox.warning(self, 'No fue posible leer la fuente', str(error))
        finally:
            self.reading = False
            for widget in (self.read_button, self.buttons, self.scope, self.codes, self.select_all_button, self.deselect_all_button):
                widget.setEnabled(True)

    def filter_codes(self, *_):
        scope = self.scope.currentData()
        members = scope_members(scope) if scope is not None else ()
        for item in self.items():
            code = item.data(0, Qt.UserRole)
            item.setHidden((scope != 'all' and sector_scope(code) not in members) or self.search.text().strip() not in code)
        self.update_summary()

    def set_visible_checked(self, checked):
        previous = self.codes.blockSignals(True)
        try:
            for item in self.items():
                if not item.isHidden():
                    item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        finally:
            self.codes.blockSignals(previous)
        self.update_summary()

    def clear_codes(self):
        previous = self.codes.blockSignals(True)
        try:
            for item in self.items():
                item.setCheckState(0, Qt.Unchecked)
        finally:
            self.codes.blockSignals(previous)
        self.update_summary()

    def update_summary(self, *_):
        selected = self.selected_prefixes()
        self.summary.setText(f'{len(selected)} códigos seleccionados. Seleccionar/deseleccionar todo actúa sobre los visibles. Sin códigos marcados se incluyen todos los del ámbito elegido.')
        scope = self.scope.currentData()
        lines = []
        for label, data in (('Fuente de validación', self.statistics), ('R1', self.r1_statistics)):
            if data is None:
                lines.append(label + ': estadísticas no disponibles.')
                continue
            count = included_count(data, scope, selected) if scope is not None else 0
            total = data['total']; percent = 100 * count / total if total else 0
            text = f'{count:,} de {total:,}'.replace(',', '.')
            lines.append(f'{label}: {text} ({percent:.1f} %)')
        self.selection_statistics.setText('Registros incluidos con este filtro:\n' + '\n'.join(lines))

    def accept(self):
        if self.reading:
            return
        scope = self.scope.currentData()
        if scope is None:
            QMessageBox.warning(self, 'Seleccione el ámbito', 'Marque al menos un ámbito o Todos.')
            return
        members = scope_members(scope)
        if scope != 'all' and any(sector_scope(code) not in members for code in self.selected_prefixes()):
            QMessageBox.warning(self, 'Selección incompatible', 'Hay códigos marcados de otro ámbito. Quite esa selección o marque el ámbito correspondiente.')
            return
        super().accept()

    def reject(self):
        if not self.reading:
            super().reject()

    def closeEvent(self, event):
        if self.reading:
            event.ignore()
        else:
            super().closeEvent(event)
