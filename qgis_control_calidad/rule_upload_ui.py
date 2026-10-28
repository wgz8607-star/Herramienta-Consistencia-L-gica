"""Administrative preview and insert-only Excel import; no rule SQL is executed."""
from contextlib import closing
import shutil

from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)
try:
    import psycopg2
except ImportError:
    psycopg2 = None
from .rule_upload import TABLES, TEMPLATE, create_template, read_rules, fetch_existing, preview_import, insert_import


def inspect_file(params, table, filename):
    if psycopg2 is None:
        raise RuntimeError('Se requiere psycopg2 para consultar el repositorio.')
    rules = read_rules(filename)
    with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection:
            return preview_import(connection, table, rules)


def export_existing(params, table, filename):
    if psycopg2 is None:
        raise RuntimeError('Se requiere psycopg2 para consultar el repositorio.')
    with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection:
            records = fetch_existing(connection, table)
    create_template(filename, records)
    return len(records)


def apply_plan(params, plan):
    if psycopg2 is None:
        raise RuntimeError('Se requiere psycopg2 para consultar el repositorio.')
    with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
        with connection:
            return insert_import(connection, plan)


class RuleUploadPage(QWidget):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.plan = None
        layout = QVBoxLayout(self)
        intro = QLabel('Administración de sentencias · Repositorio de reglas')
        intro.setStyleSheet('font-size: 18px; font-weight: 700; color: #0468A3;')
        layout.addWidget(intro)
        note = QLabel('Use una fila por regla con todos sus campos. Puede descargar una plantilla vacía o exportar todas las reglas de la tabla, incluidas las inactivas y versiones no publicadas. La carga incorpora únicamente reglas nuevas; las existentes se conservan. Las consultas se guardan sin ejecutarlas.')
        note.setWordWrap(True); layout.addWidget(note)
        target = QHBoxLayout(); target.addWidget(QLabel('Destino · base sentencias'))
        self.destination = QComboBox(); self.destination.addItems(['public.' + table for table in TABLES])
        target.addWidget(self.destination, 1); layout.addLayout(target)
        actions = QHBoxLayout()
        self.template_button = QPushButton('Descargar plantilla Excel')
        self.export_button = QPushButton('Exportar todas las reglas')
        self.preview_button = QPushButton('Leer Excel y revisar carga')
        actions.addWidget(self.template_button); actions.addWidget(self.export_button); actions.addWidget(self.preview_button)
        layout.addLayout(actions)
        self.summary = QLabel('Seleccione el destino y un Excel para revisar. La escritura requiere permisos de administración sobre la tabla.')
        self.summary.setWordWrap(True); layout.addWidget(self.summary)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(['Fila Excel', 'Versión', 'Componente', 'Código', 'Tipo', 'Activa', 'Orden', 'Resultado'])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        layout.addWidget(self.table, 1)
        layout.addWidget(QLabel('Sentencia de la fila seleccionada'))
        self.sql_text = QPlainTextEdit(); self.sql_text.setReadOnly(True); self.sql_text.setMaximumHeight(170)
        layout.addWidget(self.sql_text)
        self.insert_button = QPushButton('Incorporar reglas nuevas')
        self.insert_button.setEnabled(False)
        self.insert_button.setStyleSheet('QPushButton:disabled { background: #C4CDD4; color: #65737E; }')
        layout.addWidget(self.insert_button)
        self.destination.currentTextChanged.connect(self.clear_plan)
        self.template_button.clicked.connect(self.download_template)
        self.export_button.clicked.connect(self.download_existing)
        self.preview_button.clicked.connect(self.preview)
        self.insert_button.clicked.connect(self.incorporate)
        self.table.itemSelectionChanged.connect(self.show_sql)

    def clear_plan(self, *_):
        self.plan = None; self.insert_button.setEnabled(False); self.table.setRowCount(0); self.sql_text.clear()
        self.summary.setText('Seleccione un Excel y revise las filas antes de incorporarlas.')

    def available(self):
        if self.owner.controls_running or self.owner.exporting or self.owner.repository_upload_busy:
            QMessageBox.information(self, 'Proceso en curso', 'Espere a que termine el proceso actual antes de administrar las reglas.')
            return False
        return True

    def task(self, function, *args):
        self.owner.repository_upload_busy = True
        self.owner.main_tabs.setEnabled(False)
        try:
            return self.owner.report_task(function, *args)
        finally:
            self.owner.repository_upload_busy = False
            self.owner.main_tabs.setEnabled(True)

    def save_path(self, name):
        path, _ = QFileDialog.getSaveFileName(self, 'Guardar Excel de reglas', name, 'Excel (*.xlsx)')
        return path if not path or path.lower().endswith('.xlsx') else path + '.xlsx'

    def download_template(self):
        if not self.available():
            return
        path = self.save_path('plantilla_reglas.xlsx')
        if path:
            try:
                shutil.copyfile(TEMPLATE, path)
                self.summary.setText('Plantilla guardada: ' + path)
            except Exception as error:
                QMessageBox.warning(self, 'No se guardó la plantilla', str(error))

    def download_existing(self):
        if not self.available():
            return
        params = self.owner.repository_connection_params()
        if params is None:
            return
        path = self.save_path(self.destination.currentText() + '.xlsx')
        if path:
            try:
                count = self.task(export_existing, params, self.destination.currentText().split('.', 1)[1], path)
                self.summary.setText(f'Exportadas {count} reglas con todos sus campos: ' + path)
            except Exception as error:
                QMessageBox.warning(self, 'No se exportaron las reglas', str(error))

    def preview(self):
        if not self.available():
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Seleccione el Excel de reglas', '', 'Excel (*.xlsx)')
        if not path:
            return
        self.clear_plan()
        params = self.owner.repository_connection_params()
        if params is None:
            return
        try:
            self.plan = self.task(inspect_file, params, self.destination.currentText().split('.', 1)[1], path)
        except Exception as error:
            self.summary.setText('No se cargaron reglas. Corrija el archivo o el acceso al repositorio.')
            QMessageBox.warning(self, 'No se pudo preparar la carga', str(error))
            return
        self.table.setRowCount(len(self.plan.rules))
        for row, (rule, state) in enumerate(zip(self.plan.rules, self.plan.states)):
            values = rule.values
            for column, value in enumerate((rule.row, values[0], values[1], values[2], values[3], 'Sí' if values[6] else 'No', values[7], state)):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        publications = {r[0]: r[9] for r in self.plan.inserts}
        metadata = '; '.join(version + ': ' + ('publicada' if published else 'sin publicar') for version, published in sorted(publications.items()))
        self.summary.setText(f'{len(self.plan.rules)} filas leídas · {len(self.plan.inserts)} nuevas · {len(self.plan.rules)-len(self.plan.inserts)} existentes que se conservarán. ' + metadata)
        self.insert_button.setEnabled(bool(self.plan.inserts))
        if self.plan.rules:
            self.table.selectRow(0)

    def show_sql(self):
        row = self.table.currentRow()
        self.sql_text.setPlainText(self.plan.rules[row].values[4] if self.plan and 0 <= row < len(self.plan.rules) else '')

    def incorporate(self):
        if not self.available() or not self.plan or not self.plan.inserts:
            return
        answer = QMessageBox.question(self, 'Incorporar reglas revisadas',
            f'Se incorporarán {len(self.plan.inserts)} reglas nuevas en public.{self.plan.table}, base sentencias. Las existentes no se modificarán. ¿Continuar?',
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if answer != QMessageBox.Yes:
            return
        params = self.owner.repository_connection_params()
        if params is None:
            return
        try:
            count = self.task(apply_plan, params, self.plan)
        except Exception as error:
            self.clear_plan()
            self.summary.setText('La carga no se aplicó. Revise nuevamente antes de reintentar.')
            QMessageBox.warning(self, 'No se incorporaron las reglas', str(error))
            return
        self.clear_plan()
        self.summary.setText(f'{count} reglas incorporadas. Vuelva a seleccionar la versión de sentencias para utilizarlas.')
        self.owner.clear_repository_rules()
