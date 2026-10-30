"""Filter editor and read-only discovery of NPN prefixes from the selected source."""
import csv
import re
from contextlib import closing

import psycopg2
from psycopg2 import sql
from qgis.PyQt.QtCore import Qt, QSize, pyqtSignal
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QToolButton, QMenu, QWidgetAction, QWidget, QCheckBox, QTreeWidget, QTreeWidgetItem, QHeaderView, QSizePolicy, QGridLayout, QScrollArea, QFrame, QAbstractItemView)
from .territorial_scope import SCOPES, NPN_COLUMNS, normalize_prefixes, scope_members, sector_scope
from .territorial_statistics import included_count, prefix_counts, selected_statistics


def prefixes_from_values(values):
    return sorted({str(value).strip()[:17] for value in values
                   if value is not None and re.fullmatch(r'[0-9]{17}', str(value).strip()[:17])})


def read_prefixes(params, schema, model, snapshot=None):
    if snapshot is not None:
        column = next((name for name in NPN_COLUMNS if name in snapshot.columns), None)
        if column is None:
            raise ValueError('La tabla de predios no contiene una columna NPN.')
        index = snapshot.columns.index(column)
        with snapshot.csv_path.open(encoding='utf-8', newline='') as stream:
            return prefixes_from_values(row[index] for row in csv.reader(stream) if len(row) > index)
    if not schema:
        raise ValueError('Seleccione el esquema a validar o cargue la base catastral CICA antes de leer los códigos.')
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
                raise ValueError(f'{table}: no se encontró una columna NPN en la tabla seleccionada.')
            cursor.execute(sql.SQL("SELECT DISTINCT substring(btrim({}::text), 1, 17) FROM {} WHERE substring(btrim({}::text), 1, 17) ~ '^[0-9]{{17}}$' ORDER BY 1").format(
                sql.Identifier(column), sql.Identifier(schema, table), sql.Identifier(column)))
            return [row[0] for row in cursor.fetchall()]


BASE_COLOR = '#217346'
R1_COLOR = '#0066B3'


def color_columns(item, base_column, r1_column):
    item.setForeground(base_column, QColor(BASE_COLOR))
    item.setBackground(base_column, QColor('#EAF5EC'))
    item.setForeground(r1_column, QColor(R1_COLOR))
    item.setBackground(r1_column, QColor('#EAF2FC'))


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
        self.setText(SCOPES.get(self.currentData(), 'Seleccione alcance…'))


class TerritorialOverview(QWidget):
    """Compact source/R1 counts, shared by the summary tab and the detail window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('territorialOverview')
        self.setStyleSheet('QWidget#territorialOverview { background: white; border: 1px solid #DCE4EC; border-radius: 10px; }')
        layout = QVBoxLayout(self); layout.setContentsMargins(12, 14, 12, 12); layout.setSpacing(12)
        self.statistics_bundle = {}
        self.applied_scope = 'all'
        self.applied_prefixes = ()
        self.validation_overview = False
        title = QLabel('Distribución por alcance')
        self.title = title
        title.setStyleSheet('color: #243B53; font-weight: 700; font-size: 16px; border: none;')
        layout.addWidget(title)
        cards = QHBoxLayout(); cards.setSpacing(10)
        self.source_label = QLabel(); self.r1_label = QLabel()
        self.total_labels = {}
        self.coverage_labels = {}
        for key, caption, detail, color, background in (
            ('source', 'Base catastral a validar', self.source_label, BASE_COLOR, '#EDF8F1'),
            ('r1', 'R1 · Predios únicos', self.r1_label, R1_COLOR, '#EDF5FF')):
            card = QFrame(); card.setObjectName(key + 'OverviewCard')
            card.setStyleSheet(f'QFrame#{key}OverviewCard {{ background: {background}; border: 1px solid {color}; border-left: 5px solid {color}; border-radius: 8px; }}')
            card_layout = QVBoxLayout(card); card_layout.setContentsMargins(12, 12, 10, 12); card_layout.setSpacing(5)
            label = QLabel(caption); label.setWordWrap(True)
            label.setStyleSheet(f'color: {color}; font-weight: 700; font-size: 13px; border: none;')
            value = QLabel('—'); value.setStyleSheet(f'color: {color}; font-size: 29px; font-weight: 700; border: none;')
            self.total_labels[key] = value
            detail.setWordWrap(True); detail.setTextFormat(Qt.PlainText)
            detail.setStyleSheet(f'color: {color}; font-size: 11px; border: none;')
            coverage = QLabel(); coverage.setWordWrap(True)
            coverage.setStyleSheet(f'color: {color}; font-size: 11px; border: none;')
            coverage.hide(); self.coverage_labels[key] = coverage
            card_layout.addWidget(label); card_layout.addWidget(value); card_layout.addWidget(coverage); card_layout.addWidget(detail)
            cards.addWidget(card, 1)
        layout.addLayout(cards)
        self.table = QTreeWidget(); self.table.setRootIsDecorated(False)
        self.table.setHeaderLabels(['Alcance', 'Base catastral\na validar', 'R1 únicos'])
        color_columns(self.table.headerItem(), 1, 2)
        self.table.header().setSectionResizeMode(QHeaderView.Stretch)
        self.table.header().setMinimumHeight(42)
        self.table.headerItem().setToolTip(1, "Base catastral a validar: conteo de registros")
        self.table.setMinimumHeight(226); self.table.setMaximumHeight(226)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet('QTreeWidget { background: white; border: 1px solid #DCE4EC; border-radius: 6px; font-size: 12px; } QHeaderView::section { background: #F0F4F8; padding: 7px 3px; border: none; border-bottom: 1px solid #DCE4EC; font-weight: 700; }')
        self.rows = {}
        for key, label in (('total', 'Total'), ('urban', 'Urbano'), ('rural', 'Rural'), ('center', 'Centro poblado'), ('unknown', 'Sin alcance')):
            item = QTreeWidgetItem([label, '—', '—']); color_columns(item, 1, 2)
            item.setSizeHint(0, QSize(0, 35))
            item.setBackground(0, QColor('#F7F9FC'))
            for column in (1, 2):
                item.setTextAlignment(column, Qt.AlignCenter)
            if key == 'total':
                for column in range(3):
                    font = QFont(item.font(column)); font.setBold(True); font.setPointSize(11)
                    item.setFont(column, font)
                item.setBackground(0, QColor('#E8EEF5'))
                item.setBackground(1, QColor('#D3EEDD'))
                item.setBackground(2, QColor('#D5E8FF'))
            self.table.addTopLevelItem(item); self.rows[key] = item
        layout.addWidget(self.table)
        self.note = QLabel('Base catastral: activos y cancelados pendientes de consultar — R1: pendiente de consultar.')
        self.note.setTextFormat(Qt.RichText)
        self.note.setStyleSheet('background: #F7F9FC; border: 1px solid #E4EAF0; border-radius: 6px; padding: 9px; font-size: 12px;')
        self.note.setWordWrap(True); layout.addWidget(self.note)
        self.r1_note = QLabel(); self.r1_note.setWordWrap(True); layout.addWidget(self.r1_note)
        self.r1_note.setStyleSheet(f"color: {R1_COLOR};")
        self.set_statistics(None)

    def set_filter(self, scope, prefixes=()):
        scope_members(scope)
        self.validation_overview = True
        self.applied_scope = scope
        self.applied_prefixes = tuple(prefixes)
        self.title.setText('Alcance a validar')
        self.set_statistics(self.statistics_bundle)

    def set_statistics(self, bundle):
        bundle = bundle or {}
        self.statistics_bundle = bundle
        original_source = bundle.get('source_statistics'); original_r1 = bundle.get('r1_statistics')
        filtered = self.validation_overview and (self.applied_scope != 'all' or bool(self.applied_prefixes))
        source = selected_statistics(original_source, self.applied_scope, self.applied_prefixes) if filtered and original_source is not None else original_source
        r1 = selected_statistics(original_r1, self.applied_scope, self.applied_prefixes) if filtered and original_r1 is not None else original_r1
        for key, original, selected in (('source', original_source, source), ('r1', original_r1, r1)):
            coverage = self.coverage_labels[key]
            coverage.setVisible(self.validation_overview)
            if original is None:
                coverage.setText('Estadísticas pendientes')
            else:
                percentage = 100 * selected['total'] / original['total'] if original['total'] else 0
                coverage.setText(f"de {original['total']:,} disponibles · {percentage:.1f} %".replace(',', '.'))
        self.source_label.setText('Base catastral a validar: ' + (source['source'] if source is not None else bundle.get('source_error') or 'pendiente de consultar'))
        self.r1_label.setText('R1: ' + (r1['source'] if r1 is not None else bundle.get('r1_status') or 'pendiente de consultar'))
        for key, data in (('source', source), ('r1', r1)):
            self.total_labels[key].setText('—' if data is None else f"{data['total']:,}".replace(',', '.'))
        for column, data in ((1, source), (2, r1)):
            for key, item in self.rows.items():
                value = None if data is None else data['total'] if key == 'total' else data['totals'][key]
                item.setText(column, '—' if value is None else f'{value:,}'.replace(',', '.'))
        statuses = source.get('status_counts', {}) if source is not None else {}
        def number(value):
            return 'no disponible' if value is None else f'{value:,}'.replace(',', '.')
        base_text = ('Base catastral: ' + number(statuses.get('active')) + ' predios activos; ' +
                     number(statuses.get('cancelled')) + ' predios cancelados' +
                     (f"; otros/sin estado: {number(statuses['other'])}" if statuses.get('other') else ''))
        r1_text = 'R1: ' + number(r1['total'] if r1 is not None else None) + ' predios (NPN únicos).'
        if filtered:
            base_text = 'Base catastral: ' + number(source['total'] if source is not None else None) + ' registros incluidos de ' + number(original_source['total'] if original_source is not None else None)
            r1_text = 'R1: ' + number(r1['total'] if r1 is not None else None) + ' predios únicos incluidos de ' + number(original_r1['total'] if original_r1 is not None else None) + '.'
        self.note.setText(f'<span style="color:{BASE_COLOR}">{base_text}</span> — <span style="color:{R1_COLOR}">{r1_text}</span>')
        self.note.setToolTip('Cantidades del alcance y los códigos aplicados. El detalle de la fuente completa sigue disponible en la ventana de estadísticas.' if filtered else statuses.get('method', 'Estado de la base catastral no disponible.'))
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
        self.cica_stage_note = QLabel()
        self.cica_stage_note.setWordWrap(True)
        self.cica_stage_note.hide()
        layout.addWidget(self.cica_stage_note)
        self.cica_stages = QTreeWidget()
        self.cica_stages.setHeaderLabels(['DIVIPOLA', 'Zona', 'Código zona (6–7)', 'Etapa', 'Total predios', 'Activos', 'Cancelados', 'Otros estados'])
        self.cica_stages.setAlternatingRowColors(True)
        self.cica_stages.setRootIsDecorated(False)
        self.cica_stages.setMinimumHeight(200)
        self.cica_stages.setStyleSheet('QHeaderView::section { background: #217346; color: white; padding: 6px; }')
        self.cica_stages.hide()
        layout.addWidget(self.cica_stages)
        form = QFormLayout(); self.scope = ScopeSelector(scope)
        form.addRow('Alcance', self.scope); layout.addLayout(form)
        explanation = QLabel('Combine alcances. Todos incluye registros sin alcance identificable. El mismo filtro se aplica a la base catastral a validar y a R1/R2. Los conteos de la base catastral a validar y de R1 se muestran separados.')
        explanation.setWordWrap(True); layout.addWidget(explanation)
        self.selection_statistics = QLabel('Predios incluidos con este filtro: pendiente de consultar.')
        self.selection_statistics.setStyleSheet('background: #f4f6f8; padding: 10px; font-weight: bold;')
        self.selection_statistics.setTextFormat(Qt.RichText)
        self.selection_statistics.setWordWrap(True); layout.addWidget(self.selection_statistics)
        text = QLabel('Manzanas / veredas (opcional): posiciones 1–17 del NPN.\nCódigos presentes en la base catastral a validar o en R1. Sin códigos marcados se incluyen todos los del alcance elegido. El mismo filtro se aplica a la base catastral a validar y a R1/R2.')
        text.setWordWrap(True); layout.addWidget(text)
        self.read_button = QPushButton('Actualizar estadísticas')
        self.read_button.clicked.connect(self.load_codes); layout.addWidget(self.read_button)
        self.search = QLineEdit(); self.search.setPlaceholderText('Buscar código de 17 dígitos…')
        self.search.textChanged.connect(self.filter_codes); layout.addWidget(self.search)
        selection_buttons = QHBoxLayout()
        self.select_all_button = QPushButton('Seleccionar todo'); self.deselect_all_button = QPushButton('Deseleccionar todo')
        self.select_all_button.clicked.connect(lambda: self.set_visible_checked(True))
        self.deselect_all_button.clicked.connect(lambda: self.set_visible_checked(False))
        for button in (self.select_all_button, self.deselect_all_button):
            button.setToolTip('Actúa sobre los códigos visibles según el alcance y la búsqueda.')
            selection_buttons.addWidget(button)
        layout.addLayout(selection_buttons)
        self.codes = QTreeWidget(); self.codes.setHeaderLabels(['Código NPN (1–17)', 'Tipo', 'Base catastral a validar', 'Predios únicos R1'])
        color_columns(self.codes.headerItem(), 2, 3)
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
                label = {'rural': 'Vereda', 'urban': 'Manzana', 'center': 'Centro poblado'}.get(category, 'Sin alcance')
                r1_count = str(r1_counts.get(code, 0)) if self.r1_statistics is not None else '—'
                source_count = str(self.counts.get(code, 0)) if self.statistics is not None else '—'
                item = QTreeWidgetItem([code, label, source_count, r1_count])
                color_columns(item, 2, 3)
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
        self.cica_stages.clear()
        has_stages = isinstance(loaded, dict) and 'cica_stages' in loaded
        self.cica_stage_note.setVisible(has_stages)
        self.cica_stages.setVisible(has_stages)
        if has_stages:
            error = loaded.get('cica_stages_error')
            self.cica_stages.setVisible(not bool(error))
            source = loaded.get('cica_stages_source', '')
            self.cica_stage_note.setText('Seguimiento CICA por etapas' + (' · ' + source if source else '') + '\n' +
                ('No disponible: ' + error if error else 'Conteos por zona y etapa registrada. Para Copia base CICA: contexto del municipio completo antes de filtrar etapas; para CSV/GDB: datos del archivo seleccionado.'))
            for row in loaded.get('cica_stages', []):
                values = []
                for index, value in enumerate(row):
                    if value is None:
                        text = '—'
                    elif 4 <= index <= 7:
                        text = f'{value:,}'.replace(',', '.') if isinstance(value, (int, float)) else str(value)
                    else:
                        text = ', '.join(map(str, value)) if isinstance(value, (list, tuple)) else str(value)
                    values.append(text)
                item = QTreeWidgetItem(values)
                for index, text in enumerate(values):
                    item.setToolTip(index, text)
                if len(values) > 3 and not values[3]:
                    item.setText(3, 'Sin etapa')
                self.cica_stages.addTopLevelItem(item)
            for index in range(8):
                self.cica_stages.resizeColumnToContents(index)
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
            QMessageBox.warning(self, 'No fue posible leer los datos', str(error))
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
        self.summary.setText(f'{len(selected)} códigos seleccionados. Seleccionar/deseleccionar todo actúa sobre los visibles. Sin códigos marcados se incluyen todos los del alcance elegido.')
        scope = self.scope.currentData()
        lines = []
        for title, data in (('Base catastral a validar (registros)', self.statistics), ('R1 (predios únicos)', self.r1_statistics)):
            if data is None:
                lines.append(title + ': estadísticas no disponibles.')
                continue
            count = included_count(data, scope, selected) if scope is not None else 0
            total = data['total']; percent = 100 * count / total if total else 0
            text = f'{count:,} de {total:,}'.replace(',', '.')
            lines.append(f'{title}: {text} ({percent:.1f} %)')
        colored = [f'<span style="color:{BASE_COLOR if index == 0 else R1_COLOR}">{line}</span>' for index, line in enumerate(lines)]
        self.selection_statistics.setText('Incluidos con el filtro seleccionado:<br>' + '<br>'.join(colored))

    def accept(self):
        if self.reading:
            return
        scope = self.scope.currentData()
        if scope is None:
            QMessageBox.warning(self, 'Seleccione el alcance', 'Marque al menos un alcance o Todos.')
            return
        members = scope_members(scope)
        if scope != 'all' and any(sector_scope(code) not in members for code in self.selected_prefixes()):
            QMessageBox.warning(self, 'Selección incompatible', 'Hay códigos marcados de otro alcance. Quite esa selección o marque el alcance correspondiente.')
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
