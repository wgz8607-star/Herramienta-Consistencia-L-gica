"""Filter editor and read-only discovery of NPN prefixes from the selected source."""
import csv
import re
from contextlib import closing

import psycopg2
from psycopg2 import sql
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QToolButton, QMenu, QWidgetAction, QWidget, QCheckBox, QTreeWidget, QTreeWidgetItem, QHeaderView, QSizePolicy, QGridLayout, QScrollArea)
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


class TerritorialOverview(QWidget):
    """Compact source/R1 counts, shared by the summary tab and the detail window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel('Distribución por ámbito')
        title.setStyleSheet('color: #0468A3; font-weight: bold; font-size: 14px;')
        layout.addWidget(title)
        self.source_label = QLabel(); self.source_label.setWordWrap(True); layout.addWidget(self.source_label)
        self.r1_label = QLabel(); self.r1_label.setWordWrap(True); layout.addWidget(self.r1_label)
        self.table = QTreeWidget(); self.table.setRootIsDecorated(False)
        self.table.setHeaderLabels(['Ámbito', 'Fuente', 'R1 únicos'])
        self.table.header().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(180); self.table.setMaximumHeight(215)
        self.rows = {}
        for key, label in (('total', 'Total'), ('urban', 'Urbano'), ('rural', 'Rural'), ('center', 'Centro poblado'), ('unknown', 'Sin ámbito')):
            item = QTreeWidgetItem([label, '—', '—']); self.table.addTopLevelItem(item); self.rows[key] = item
        layout.addWidget(self.table)
        self.note = QLabel('Fuente: registros (incluye duplicados). R1: predios únicos por NPN completo. No se suman entre fuentes.')
        self.note.setWordWrap(True); layout.addWidget(self.note)
        self.r1_note = QLabel(); self.r1_note.setWordWrap(True); layout.addWidget(self.r1_note)
        self.set_statistics(None)

    def set_statistics(self, bundle):
        bundle = bundle or {}
        source = bundle.get('source_statistics'); r1 = bundle.get('r1_statistics')
        self.source_label.setText('Fuente: ' + (source['source'] if source is not None else bundle.get('source_error') or 'pendiente de consultar'))
        self.r1_label.setText('R1: ' + (r1['source'] if r1 is not None else bundle.get('r1_status') or 'pendiente de consultar'))
        for column, data in ((1, source), (2, r1)):
            for key, item in self.rows.items():
                value = None if data is None else data['total'] if key == 'total' else data['totals'][key]
                item.setText(column, '—' if value is None else f'{value:,}'.replace(',', '.'))
        if r1 is None:
            self.r1_note.setText('Las estadísticas de R1 se mostrarán al consultar su origen.')
        else:
            self.r1_note.setText(f"R1: {r1.get('duplicates', 0):,} duplicados no sumados · {r1.get('missing_npn', 0):,} filas sin NPN excluidas.".replace(',', '.'))


class TerritorialFilterDialog(QDialog):
    filterApplied = pyqtSignal(str, object)
    resetRequested = pyqtSignal()

    def __init__(self, scope, prefixes, loader, parent=None, embedded=False):
        super().__init__(parent)
        self.setWindowTitle('Filtro avanzado — Modelo Interno / CICA')
        self.embedded = embedded
        if embedded:
            self.setWindowFlags(Qt.Widget)
        else:
            self.resize(900, 760)
            self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.loader = loader
        self.statistics = None; self.r1_statistics = None; self.r1_status = 'Pendiente de consultar R1.'; self.counts = {}; self.reading = False
        outer = QVBoxLayout(self)
        content = QWidget(); layout = QVBoxLayout(content)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidget(content); outer.addWidget(scroll)
        self.overview = TerritorialOverview()
        layout.addWidget(self.overview)
        form = QFormLayout(); self.scope = ScopeSelector(scope)
        form.addRow('Ámbito', self.scope); layout.addLayout(form)
        explanation = QLabel('Combine ámbitos. Todos incluye registros sin ámbito identificable. El mismo filtro se aplica a la fuente y a R1/R2. Los conteos de la fuente y de R1 se muestran separados.')
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
        self.codes = QTreeWidget(); self.codes.setHeaderLabels(['Código NPN (1–17)', 'Tipo', 'Registros fuente', 'Predios únicos R1'])
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
        self.buttons.button(QDialogButtonBox.Cancel).setText('Restablecer' if embedded else 'Cancelar')
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.resetRequested.emit if embedded else self.reject)
        outer.addWidget(self.buttons)
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
                r1_count = str(r1_counts.get(code, 0)) if self.r1_statistics is not None else '—'
                source_count = str(self.counts.get(code, 0)) if self.statistics is not None else '—'
                item = QTreeWidgetItem([code, label, source_count, r1_count])
                item.setData(0, Qt.UserRole, code)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Checked if code in selected else Qt.Unchecked)
                self.codes.addTopLevelItem(item)
        finally:
            self.codes.blockSignals(previous)
        self.filter_codes()

    def invalidate_statistics(self, scope, prefixes):
        self.statistics = None; self.r1_statistics = None; self.counts = {}
        self.r1_status = 'Pendiente de actualizar.'
        self.overview.set_statistics(None)
        self.scope.set_scope(scope)
        self.populate(prefixes, prefixes)

    def set_statistics(self, loaded):
        selected = self.selected_prefixes()
        if isinstance(loaded, dict) and 'source_statistics' in loaded:
            self.statistics = loaded.get('source_statistics')
            self.r1_statistics = loaded.get('r1_statistics')
            self.r1_status = loaded.get('r1_status', '')
            self.overview.set_statistics(loaded)
            codes = []
        else:
            self.statistics = loaded if isinstance(loaded, dict) else None
            self.r1_statistics = None; self.r1_status = 'R1 no consultado.'
            self.overview.set_statistics({'source_statistics': self.statistics, 'r1_status': self.r1_status})
            codes = loaded if isinstance(loaded, list) else []
        self.counts = prefix_counts(self.statistics) if self.statistics is not None else {}
        codes = sorted(set(codes) | set(self.counts) | (set(prefix_counts(self.r1_statistics)) if self.r1_statistics is not None else set()))
        if set(selected) - set(codes):
            QMessageBox.warning(self, 'Códigos no encontrados', 'Algunos códigos marcados no aparecen en los orígenes consultados. Se conservarán marcados; revise la selección.')
        self.populate(sorted(set(codes) | set(selected)), selected)
        self.update_summary()

    def load_codes(self):
        if self.reading:
            return
        self.reading = True
        for widget in (self.read_button, self.buttons, self.scope, self.codes, self.select_all_button, self.deselect_all_button):
            widget.setEnabled(False)
        try:
            self.set_statistics(self.loader())
        except Exception as error:
            self.statistics = None; self.r1_statistics = None; self.counts = {}
            self.r1_status = 'Estadísticas no disponibles.'
            self.overview.set_statistics({'source_error': str(error), 'r1_status': self.r1_status})
            for item in self.items():
                item.setText(2, '—'); item.setText(3, '—')
            self.update_summary()
            QMessageBox.warning(self, 'No fue posible leer las fuentes', str(error))
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
        for title, data in (('Fuente (registros)', self.statistics), ('R1 (predios únicos)', self.r1_statistics)):
            if data is None:
                lines.append(title + ': estadísticas no disponibles.')
                continue
            count = included_count(data, scope, selected) if scope is not None else 0
            total = data['total']; percent = 100 * count / total if total else 0
            text = f'{count:,} de {total:,}'.replace(',', '.')
            lines.append(f'{title}: {text} ({percent:.1f} %)')
        self.selection_statistics.setText('Incluidos con el filtro seleccionado:\n' + '\n'.join(lines))

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
        if self.embedded:
            self.filterApplied.emit(scope, self.selected_prefixes())
        else:
            super().accept()

    def reject(self):
        if not self.reading:
            super().reject()

    def closeEvent(self, event):
        if self.reading:
            event.ignore()
        else:
            super().closeEvent(event)
