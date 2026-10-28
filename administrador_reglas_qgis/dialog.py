from pathlib import Path
import shutil

from qgis.PyQt.QtCore import QObject, QThread, Qt, pyqtSignal, pyqtSlot
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout,
)
from .conexiones import connection_names, saved_connection_params
from .repositorio import COLUMNS, TEMPLATE
from . import servicio


class Task(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, function, args):
        super().__init__(); self.function = function; self.args = args

    @pyqtSlot()
    def run(self):
        try:
            self.result.emit(self.function(*self.args))
        except Exception as error:
            self.error.emit(str(error) or type(error).__name__)
        finally:
            self.finished.emit()


class AdministratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Administrador de Reglas SQL')
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.setWindowIcon(QIcon(str(Path(__file__).parent / 'icon.svg')))
        self.resize(1120, 800)
        self.setStyleSheet(
            "QWidget { font-size: 12px; } QDialog { background: #F5F7FA; } "
            "QGroupBox { border: 1px solid #DCE3EB; border-radius: 4px; margin-top: 10px; padding-top: 8px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 8px; color: #0468A3; font-weight: 600; } "
            "QLineEdit, QComboBox { background: white; border: 1px solid #AFC8D8; border-radius: 3px; padding: 3px; } "
            "QPushButton { background: #068CBB; color: white; border: none; border-radius: 4px; padding: 6px 10px; } "
            "QPushButton:hover { background: #0468A3; } QPushButton:disabled { background: #CDD6DD; color: #697782; } "
            "QHeaderView::section { background: #068CBB; color: white; padding: 4px; border: none; }")
        self.busy = False; self.plan = None; self.thread = None; self.worker = None
        self.close_when_idle = False; self.after_task = None; self.secrets = []
        self._build(); self.refresh_connections()

    def _build(self):
        layout = QVBoxLayout(self)
        heading = QLabel('Administrador de Reglas SQL')
        heading.setStyleSheet('font-size: 21px; font-weight: 700; color: #0468A3;')
        layout.addWidget(heading)
        note = QLabel('Complemento independiente del validador. Seleccione la conexión, el esquema y una tabla de reglas existente. Se incorporan filas nuevas o se reemplazan las que coincidan en versión, componente y orden, siempre con vista previa y confirmación. El SQL importado no se ejecuta.')
        note.setWordWrap(True); layout.addWidget(note)
        top = QHBoxLayout(); layout.addLayout(top)
        self.connection_box = QGroupBox('1. Conexión PostgreSQL'); top.addWidget(self.connection_box, 1)
        form = QFormLayout(self.connection_box)
        self.mode = QComboBox(); self.mode.addItems(['Conexión guardada en QGIS', 'Parámetros de conexión'])
        form.addRow('Forma de conexión', self.mode)
        self.pages = QStackedWidget(); form.addRow(self.pages)
        saved = QGroupBox(); saved_layout = QHBoxLayout(saved)
        saved_layout.setContentsMargins(0, 0, 0, 0)
        self.saved = QComboBox(); self.refresh = QPushButton('Actualizar')
        saved_layout.addWidget(self.saved, 1); saved_layout.addWidget(self.refresh)
        self.pages.addWidget(saved)
        manual = QGroupBox(); manual_layout = QFormLayout(manual)
        self.host = QLineEdit(); self.host.setPlaceholderText('Servidor o dirección IP')
        self.port = QLineEdit('5432'); self.database = QLineEdit('sentencias')
        self.user = QLineEdit(); self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password)
        self.ssl = QComboBox()
        for title, value in [('Preferir SSL', 'prefer'), ('Requerir SSL', 'require'), ('Verificar certificado y host', 'verify-full'), ('Sin SSL', 'disable')]:
            self.ssl.addItem(title, value)
        for label, field in [('Servidor', self.host), ('Puerto', self.port), ('Base de datos', self.database), ('Usuario', self.user), ('Contraseña', self.password), ('SSL', self.ssl)]:
            manual_layout.addRow(label, field)
        self.pages.addWidget(manual)
        self.connect_button = QPushButton('Conectar y listar esquemas'); form.addRow(self.connect_button)
        self.target_box = QGroupBox('2. Destino y archivo'); top.addWidget(self.target_box, 1)
        target = QFormLayout(self.target_box)
        self.schema = QComboBox(); self.table = QComboBox()
        target.addRow('Esquema', self.schema); target.addRow('Tabla de reglas', self.table)
        self.table_note = QLabel('Solo se listan tablas con los diez campos de la plantilla. No se crean tablas ni se conceden permisos.')
        self.table_note.setWordWrap(True); target.addRow(self.table_note)
        self.template_button = QPushButton('Guardar plantilla Excel')
        self.export_button = QPushButton('Exportar todas las reglas')
        self.preview_button = QPushButton('Seleccionar Excel y revisar')
        target.addRow(self.template_button); target.addRow(self.export_button); target.addRow(self.preview_button)
        self.file_label = QLabel('Sin archivo seleccionado'); self.file_label.setWordWrap(True); target.addRow(self.file_label)
        self.summary = QLabel('Seleccione una conexión. Se utilizará su usuario y sus permisos; no hay credenciales incorporadas.')
        self.summary.setWordWrap(True); layout.addWidget(self.summary)
        self.table_view = QTableWidget(0, 8)
        self.table_view.setHorizontalHeaderLabels(['Fila', 'Versión', 'Componente', 'Código', 'Tipo', 'Activa', 'Orden', 'Resultado'])
        self.table_view.verticalHeader().setDefaultSectionSize(24)
        self.table_view.setMinimumHeight(140)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        layout.addWidget(self.table_view, 1)
        details = QTabWidget()
        self.sql_text = QPlainTextEdit(); self.sql_text.setReadOnly(True)
        self.fields_text = QPlainTextEdit(); self.fields_text.setReadOnly(True)
        self.activity = QPlainTextEdit(); self.activity.setReadOnly(True)
        details.addTab(self.sql_text, 'Sentencia SQL'); details.addTab(self.fields_text, 'Todos los campos'); details.addTab(self.activity, 'Actividad y mensajes')
        details.setMaximumHeight(180); layout.addWidget(details)
        footer = QHBoxLayout(); layout.addLayout(footer)
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.hide(); footer.addWidget(self.progress, 1)
        self.load_button = QPushButton('Cargar y reemplazar reglas'); footer.addWidget(self.load_button)
        self.mode.currentIndexChanged.connect(self.change_mode)
        self.saved.currentTextChanged.connect(self.invalidate_connection)
        self.refresh.clicked.connect(self.refresh_connections)
        for field in (self.host, self.port, self.database, self.user, self.password):
            field.textChanged.connect(self.invalidate_connection)
        self.ssl.currentIndexChanged.connect(self.invalidate_connection)
        self.schema.currentIndexChanged.connect(self.schema_changed)
        self.table.currentIndexChanged.connect(self.invalidate_plan)
        self.connect_button.clicked.connect(self.load_schemas)
        self.template_button.clicked.connect(self.save_template)
        self.export_button.clicked.connect(self.export_rules)
        self.preview_button.clicked.connect(self.preview)
        self.load_button.clicked.connect(self.apply)
        self.table_view.itemSelectionChanged.connect(self.show_rule)
        self.update_buttons()

    def update_buttons(self):
        self.connection_box.setEnabled(not self.busy); self.target_box.setEnabled(not self.busy)
        table = self.table.currentData()
        self.export_button.setEnabled(not self.busy and bool(table))
        self.preview_button.setEnabled(not self.busy and bool(table))
        self.load_button.setEnabled(not self.busy and bool(self.plan and self.plan.changes) and bool(table and table['insert']))

    def invalidate_plan(self, *_):
        self.plan = None; self.table_view.setRowCount(0); self.sql_text.clear(); self.fields_text.clear()
        self.update_buttons()

    def invalidate_connection(self, *_):
        self.schema.blockSignals(True); self.schema.clear(); self.schema.blockSignals(False)
        self.table.clear(); self.invalidate_plan()
        self.summary.setText('Conexión cambiada. Pulse Conectar y listar esquemas.')

    def change_mode(self, index):
        self.pages.setCurrentIndex(index); self.invalidate_connection()

    def refresh_connections(self):
        current = self.saved.currentText()
        try:
            names = connection_names()
        except Exception as error:
            self.failed(str(error)); return
        self.saved.blockSignals(True); self.saved.clear(); self.saved.addItems(names)
        if current in names:
            self.saved.setCurrentText(current)
        self.saved.blockSignals(False); self.invalidate_connection()

    def params(self):
        if self.mode.currentIndex() == 0:
            params = saved_connection_params(self.saved.currentText())
        else:
            if not self.host.text().strip() or not self.database.text().strip() or not self.user.text().strip():
                raise ValueError('Indique servidor, base de datos y usuario.')
            try:
                port = int(self.port.text())
                if not 1 <= port <= 65535:
                    raise ValueError()
            except ValueError:
                raise ValueError('El puerto debe estar entre 1 y 65535.') from None
            params = dict(host=self.host.text().strip(), port=port, dbname=self.database.text().strip(),
                          user=self.user.text().strip(), password=self.password.text(), sslmode=self.ssl.currentData())
        secret = params.get('password')
        if secret and secret not in self.secrets:
            self.secrets.append(secret)
        return params

    def log(self, text):
        for secret in self.secrets:
            text = text.replace(secret, '***')
        self.activity.appendPlainText(text)
        return text

    def failed(self, text):
        text = self.log(text)
        self.summary.setText('La operación no se completó. Consulte Actividad y mensajes.')
        if not self.close_when_idle:
            QMessageBox.warning(self, 'No se completó la operación', text)

    def start_task(self, function, args, success, after=None):
        if self.busy:
            return
        self.busy = True; self.after_task = after; self.update_buttons(); self.progress.show()
        self.thread = QThread(self); self.worker = Task(function, args)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(success)
        self.worker.error.connect(self.task_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.task_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def task_failed(self, text):
        self.after_task = None; self.failed(text)

    def task_finished(self):
        self.busy = False; self.progress.hide(); self.worker = None; self.thread = None
        self.update_buttons()
        after, self.after_task = self.after_task, None
        if self.close_when_idle:
            self.close(); self.deleteLater()
        elif after:
            after()

    def load_schemas(self):
        try:
            params = self.params()
        except Exception as error:
            self.failed(str(error)); return
        self.invalidate_connection(); self.summary.setText('Consultando esquemas de la conexión…')
        self.start_task(servicio.list_schemas, (params,), self.schemas_loaded, after=self.load_tables)

    def schemas_loaded(self, names):
        self.schema.blockSignals(True); self.schema.clear(); self.schema.addItems(names)
        if 'public' in names:
            self.schema.setCurrentText('public')
        self.schema.blockSignals(False)
        self.summary.setText(f'{len(names)} esquemas disponibles.')

    def schema_changed(self, *_):
        self.table.clear(); self.invalidate_plan()
        if not self.busy:
            self.load_tables()

    def load_tables(self):
        schema = self.schema.currentText()
        if not schema or self.busy:
            return
        try:
            params = self.params()
        except Exception as error:
            self.failed(str(error)); return
        self.table.clear(); self.invalidate_plan(); self.summary.setText('Consultando tablas de reglas compatibles…')
        self.start_task(servicio.list_tables, (params, schema), self.tables_loaded)

    def tables_loaded(self, tables):
        self.table.blockSignals(True); self.table.clear()
        for name, can_insert in tables:
            self.table.addItem(name + ('' if can_insert else ' · solo lectura'), {'name': name, 'insert': can_insert})
        self.table.blockSignals(False); self.invalidate_plan()
        self.summary.setText(f'{len(tables)} tablas compatibles en {self.schema.currentText()}. ' + ('Seleccione el Excel o exporte las reglas existentes.' if tables else 'No se encontraron tablas con los diez campos de la plantilla y permiso de consulta.'))

    def save_path(self, title, filename):
        path, _ = QFileDialog.getSaveFileName(self, title, filename, 'Excel (*.xlsx)')
        return path if not path or path.lower().endswith('.xlsx') else path + '.xlsx'

    def save_template(self):
        path = self.save_path('Guardar plantilla', 'plantilla_reglas.xlsx')
        if path:
            try:
                shutil.copyfile(TEMPLATE, path)
                self.summary.setText('Plantilla guardada: ' + path)
            except Exception as error:
                self.failed(str(error))

    def target(self):
        target = self.table.currentData()
        if not target or not self.schema.currentText():
            raise ValueError('Seleccione un esquema y una tabla de reglas.')
        return self.schema.currentText(), target['name']

    def export_rules(self):
        try:
            params = self.params(); schema, table = self.target()
        except Exception as error:
            self.failed(str(error)); return
        path = self.save_path('Exportar todas las reglas', schema + '.' + table + '.xlsx')
        if path:
            self.summary.setText('Exportando todas las filas, incluidas reglas inactivas y versiones no publicadas…')
            self.start_task(servicio.export_existing, (params, table, path, schema), lambda count: self.exported(count, path))

    def exported(self, count, path):
        text = f'{count} reglas exportadas: {path}'
        self.summary.setText(text); self.log(text)

    def preview(self):
        try:
            params = self.params(); schema, table = self.target()
        except Exception as error:
            self.failed(str(error)); return
        path, _ = QFileDialog.getOpenFileName(self, 'Seleccione el Excel de reglas', '', 'Excel (*.xlsx)')
        if not path:
            return
        self.invalidate_plan(); self.file_label.setText(path); self.summary.setText('Leyendo Excel y preparando vista previa…')
        self.start_task(servicio.inspect_file, (params, table, path, schema), self.show_plan)

    def show_plan(self, plan):
        self.plan = plan; self.table_view.setRowCount(len(plan.rules))
        for row, (rule, state) in enumerate(zip(plan.rules, plan.states)):
            values = rule.values
            for column, value in enumerate((rule.row, values[0], values[1], values[2], values[3], 'Sí' if values[6] else 'No', values[7], state)):
                self.table_view.setItem(row, column, QTableWidgetItem(str(value)))
        message = f'{len(plan.rules)} filas · {len(plan.inserts)} nuevas · {len(plan.updates)} para reemplazar · {len(plan.rules)-plan.changes} sin cambios. Destino: {plan.schema}.{plan.table}.'
        if not self.table.currentData()['insert']:
            message += ' Esta conexión solo permite consultar la tabla.'
        self.summary.setText(message); self.log(message); self.update_buttons()
        if plan.rules:
            self.table_view.selectRow(0)

    def show_rule(self):
        row = self.table_view.currentRow()
        if self.plan is None or not 0 <= row < len(self.plan.rules):
            return
        rule = self.plan.rules[row]
        self.sql_text.setPlainText(rule.values[4])
        text = '\n\n'.join(column + ':\n' + (str(value) if value is not None else '(sin indicar)') for column, value in zip(COLUMNS, rule.values))
        replacements = [(old, new) for old, new in self.plan.updates if new[:3] == rule.key]
        if replacements:
            old, record = replacements[0]
            text += '\n\nCAMBIOS QUE SE APLICARÁN AL REEMPLAZAR:\n' + '\n\n'.join(column + ':\nAnterior: ' + str(before) + '\nNuevo: ' + str(after) for column, before, after in zip(COLUMNS, old, record) if before != after)
        elif self.plan.states[row] == 'Nueva':
            record = next(record for record in self.plan.inserts if record[:3] == rule.key)
        else:
            record = None
        if record:
            text += '\n\nMetadatos que se guardarán:\ndescripcion_version: ' + str(record[8]) + '\nversion_publicada: ' + ('Sí' if record[9] else 'No')
        self.fields_text.setPlainText(text)

    def apply(self):
        if self.busy or not self.plan or not self.plan.changes or not self.table.currentData()['insert']:
            return
        try:
            params = self.params(); schema, table = self.target()
        except Exception as error:
            self.failed(str(error)); return
        plan = self.plan
        if (schema, table) != (plan.schema, plan.table):
            self.invalidate_plan(); self.failed('El destino cambió. Revise el Excel nuevamente.'); return
        message = QMessageBox(self)
        message.setWindowTitle('Confirmar carga y reemplazos')
        message.setIcon(QMessageBox.Question)
        message.setTextFormat(Qt.PlainText)
        message.setText(f'Destino: {schema}.{table}\nBase: {params.get("dbname", params.get("service", ""))}\n\n'
                        f'Filas nuevas: {len(plan.inserts)}\nFilas que se reemplazarán: {len(plan.updates)}\nFilas sin cambios: {len(plan.rules)-plan.changes}')
        metadata_changes = [f'{old[0]} · orden {old[7]}: publicada ' + ('Sí' if old[9] else 'No') + ' → ' + ('Sí' if new[9] else 'No') for old, new in plan.updates if old[9] != new[9]]
        information = 'Revise los detalles. Los reemplazos coinciden en versión, componente y orden.'
        if metadata_changes:
            information += '\nCambios de publicación en las filas:\n' + '\n'.join(metadata_changes)
        message.setInformativeText(information + '\n¿Confirma la operación completa?')
        lines = []
        for record in plan.inserts:
            lines.append(f'NUEVA: versión {record[0]} · {record[1]} · orden {record[7]} · código {record[2]}\nSQL:\n{record[4]}')
        for old, new in plan.updates:
            lines.append(f'REEMPLAZA: versión {old[0]} · {old[1]} · orden {old[7]}\n' +
                         '\n\n'.join(column + ':\nAnterior: ' + str(before) + '\nNuevo: ' + str(after)
                                      for column, before, after in zip(COLUMNS, old, new) if before != after))
        message.setDetailedText('\n\n'.join(lines))
        message.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        message.setDefaultButton(QMessageBox.Cancel)
        if message.exec_() != QMessageBox.Yes:
            return
        self.invalidate_plan(); self.summary.setText('Cargando reglas revisadas…')
        self.start_task(servicio.apply_plan, (params, plan), self.loaded)

    def loaded(self, result):
        message = f"Carga terminada: {result['inserted']} nuevas · {result['updated']} reemplazadas · {result['unchanged']} sin cambios. Vuelva a consultar la versión en el validador."
        self.summary.setText(message); self.log(message)

    def closeEvent(self, event):
        if self.busy:
            QMessageBox.information(self, 'Proceso en curso', 'Espere a que termine la operación antes de cerrar.')
            event.ignore()
        else:
            self.password.clear(); self.secrets.clear(); self.invalidate_plan()
            event.accept()

    def reject(self):
        self.close()
