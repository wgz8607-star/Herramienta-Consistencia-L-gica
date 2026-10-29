"""Filter editor and read-only discovery of NPN prefixes from the selected source."""
import csv
import re
from contextlib import closing

import psycopg2
from psycopg2 import sql
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout)
from .territorial_scope import SCOPES, NPN_COLUMNS, normalize_prefixes


def prefixes_from_values(values):
    return sorted({str(value).strip()[:13] for value in values
                   if value is not None and re.fullmatch(r'[0-9]{13}', str(value).strip()[:13])})


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
            cursor.execute(sql.SQL("SELECT DISTINCT substring(btrim({}::text), 1, 13) FROM {} WHERE substring(btrim({}::text), 1, 13) ~ '^[0-9]{{13}}$' ORDER BY 1").format(
                sql.Identifier(column), sql.Identifier(schema, table), sql.Identifier(column)))
            return [row[0] for row in cursor.fetchall()]


class TerritorialFilterDialog(QDialog):
    def __init__(self, scope, prefixes, loader, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Filtro avanzado — Modelo Interno / CICA')
        self.resize(570, 560)
        self.loader = loader
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.scope = QComboBox()
        for key, label in SCOPES.items():
            self.scope.addItem(label, key)
        self.scope.setCurrentIndex(max(0, self.scope.findData(scope)))
        form.addRow('Ámbito', self.scope)
        layout.addLayout(form)
        text = QLabel('Opcional: seleccione manzanas o veredas por los primeros 13 dígitos del NPN.\nSin códigos marcados se incluyen todos los del ámbito elegido.\nEl mismo filtro se aplicará a la fuente y a R1/R2.')
        text.setWordWrap(True); layout.addWidget(text)
        self.read_button = QPushButton('Leer manzanas / veredas de la fuente')
        self.read_button.clicked.connect(self.load_codes); layout.addWidget(self.read_button)
        self.search = QLineEdit(); self.search.setPlaceholderText('Buscar código de 13 dígitos…')
        self.search.textChanged.connect(self.filter_codes); layout.addWidget(self.search)
        self.codes = QListWidget(); layout.addWidget(self.codes)
        self.populate(prefixes, prefixes)
        self.scope.currentIndexChanged.connect(self.filter_codes)
        clear = QPushButton('Quitar selección de manzanas / veredas')
        clear.clicked.connect(self.clear_codes); layout.addWidget(clear)
        self.summary = QLabel(); layout.addWidget(self.summary)
        self.codes.itemChanged.connect(self.update_summary)
        self.update_summary()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('Aplicar filtro')
        buttons.button(QDialogButtonBox.Cancel).setText('Cancelar')
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_prefixes(self):
        return normalize_prefixes(self.codes.item(i).data(Qt.UserRole) for i in range(self.codes.count())
                                  if self.codes.item(i).checkState() == Qt.Checked)

    def populate(self, codes, selected):
        self.codes.clear()
        for code in codes:
            sector = code[5:7]
            label = 'Vereda' if sector == '00' else 'Manzana' if sector == '01' else 'Centro poblado'
            item = QListWidgetItem(f'{code} — {label}')
            item.setData(Qt.UserRole, code)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if code in selected else Qt.Unchecked)
            self.codes.addItem(item)
        self.filter_codes()

    def load_codes(self):
        selected = self.selected_prefixes()
        self.read_button.setEnabled(False)
        try:
            codes = self.loader()
            missing = set(selected) - set(codes)
            if missing:
                QMessageBox.warning(self, 'Códigos no encontrados', 'Algunos códigos seleccionados no aparecen en esta fuente. Se conservarán marcados; revise la selección.')
            self.populate(sorted(set(codes) | set(selected)), selected)
            self.update_summary()
            if not codes:
                QMessageBox.information(self, 'Sin códigos', 'No se encontraron prefijos NPN válidos de 13 dígitos en la fuente.')
        except Exception as error:
            QMessageBox.warning(self, 'No fue posible leer la fuente', str(error))
        finally:
            self.read_button.setEnabled(True)

    def filter_codes(self, *_):
        scope = self.scope.currentData()
        for index in range(self.codes.count()):
            item = self.codes.item(index); code = item.data(Qt.UserRole); sector = code[5:7]
            matches = scope == 'all' or (scope == 'urban' and sector == '01') or (scope == 'rural' and sector == '00') or (scope == 'center' and sector > '01')
            item.setHidden(not matches or self.search.text().strip() not in code)

    def clear_codes(self):
        for index in range(self.codes.count()):
            self.codes.item(index).setCheckState(Qt.Unchecked)

    def update_summary(self, *_):
        self.summary.setText(f'{len(self.selected_prefixes())} códigos seleccionados (incluye selecciones ocultas por la búsqueda).')

    def accept(self):
        scope = self.scope.currentData()
        incompatible = [code for code in self.selected_prefixes() if not (scope == 'all' or
                        scope == 'urban' and code[5:7] == '01' or scope == 'rural' and code[5:7] == '00' or scope == 'center' and code[5:7] > '01')]
        if incompatible:
            QMessageBox.warning(self, 'Selección incompatible', 'Hay códigos marcados de otro ámbito. Quite esa selección o elija Todos.')
            return
        super().accept()
