from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from qgis.PyQt.QtCore import QObject, QSize, QThread, Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QApplication, QAbstractItemView, QComboBox, QDialog, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMessageBox, QPushButton, QProgressBar, QScrollArea, QSplitter,
    QHeaderView, QMenu, QSizePolicy, QStackedWidget, QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)
from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsSettings
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from .ingestion import CicaIngestionDialog
from .reference import ReferenceDialog
from .review_imports import ReviewImports
from .review import build_cases, digest, save_review, load_review, restore_review, REVIEW_FIELDS, display, review_statistics, statistics_row, STAT_HEADERS
from .report_exceptions import HEADERS as EXCEPTION_HEADERS, FIELDS as EXCEPTION_FIELDS, DEFAULTS as EXCEPTION_DEFAULTS, add_controls, link_rule_reviews

try:
    import psycopg2
except ImportError:
    psycopg2 = None


PLUGIN_DIR = Path(__file__).resolve().parent
SQL_ROOT = PLUGIN_DIR / "resources" / "sql"
DIVIPOLA_FILE = PLUGIN_DIR / "resources" / "data" / "divipola.xlsx"
MODELS = {"Modelo Interno de Levantamiento 1.0": "rules_int_model", "CICA": "rules_cica_db"}
SNC_CATEGORY = "Cargue SNC"
SNC_ENVIRONMENT = "Validaciones para cargue a SNC"
SNC_REPOSITORY_TABLES = {
    "CICA": "reglas_cargue_snc_cica",
    "Modelo Interno de Levantamiento 1.0": "reglas_cargue_snc_xtf",
}

SQL_REPOSITORIES = {
    "Modelo Interno de Levantamiento 1.0": ("sql_modelo_interno", "sql_modelo_interno_prueba"),
    "CICA": ("sql_cica", "sql_cica_prueba"),
}
SQL_REPOSITORY_TABLES = {
    "Modelo Interno de Levantamiento 1.0": ("reglas_interno_v3_07_09_2026", "reglas_interno_v2_29_07_2024"),
    "CICA": ("reglas_cica_v3_07_09_2026", "reglas_cica_v2_29_07_2024"),
}
REPOSITORY_CONNECTION = {
    "host": "172.19.3.225",
    "port": "5432",
    "dbname": "sentencias",
    "user": "admin_ant",
    "password": "ant12726",
}


@dataclass
class RuleResult:
    rule: str
    category: str
    status: str
    findings: int | str
    detail: str = ""
    rows: list[dict] | None = None
    description: str = ""
    criterion_hash: str = ""
    identity_safe: bool = True


class SqlVersionDialog(QDialog):
    """Busca y permite seleccionar una versión publicada del repositorio SQL."""

    def __init__(self, parent, params, repository_source):
        super().__init__(parent)
        self.params = params
        self.repository_source = repository_source
        self.selected_version = None
        self.setWindowTitle("Seleccionar versión de sentencias SQL")
        self.resize(720, 390)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Versiones publicadas en el repositorio: {repository_source['label']}"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar por versión o descripción…")
        self.search.textChanged.connect(self.filter_rows)
        layout.addWidget(self.search)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Versión", "Descripción", "Estado", "Publicada"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemDoubleClicked.connect(lambda _: self.accept_selection())
        layout.addWidget(self.table)
        controls = QHBoxLayout()
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.load_versions)
        choose = QPushButton("Usar esta versión")
        choose.clicked.connect(self.accept_selection)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        controls.addWidget(refresh); controls.addStretch(); controls.addWidget(cancel); controls.addWidget(choose)
        layout.addLayout(controls)
        self.load_versions()

    def load_versions(self):
        self.table.setRowCount(0)
        try:
            with psycopg2.connect(**self.params, connect_timeout=8) as connection:
                with connection.cursor() as cursor:
                    if self.repository_source["kind"] == "tables":
                        rows = []
                        for table in self.repository_source["tables"]:
                            published = "NULL" if self.repository_source.get("snc") else "max(fecha_actualizacion) OVER (PARTITION BY version)"
                            cursor.execute(
                                f"WITH cabeceras AS ("
                                f"SELECT DISTINCT ON (version) version, descripcion_version, version_publicada, "
                                f"{published} AS publicada FROM public.{table} "
                                "ORDER BY version, orden NULLS LAST, componente, codigo_regla"
                                ") SELECT cabecera.version, COALESCE(cabecera.descripcion_version, ''), "
                                "'PUBLICADA', cabecera.publicada FROM cabeceras AS cabecera "
                                "WHERE cabecera.version_publicada IS TRUE AND EXISTS ("
                                f"SELECT 1 FROM public.{table} AS regla "
                                "WHERE regla.version = cabecera.version AND regla.activa) "
                                "ORDER BY cabecera.publicada DESC NULLS LAST, cabecera.version DESC"
                            )
                            rows.extend(({"table": table, "version": item[0]}, item[0], item[1], item[2], item[3]) for item in cursor.fetchall())
                    else:
                        cursor.execute(
                            f"SELECT id, codigo, COALESCE(descripcion, ''), estado, fecha_publicacion "
                            f"FROM {self.repository_source['schema']}.versiones WHERE estado = 'PUBLICADA' ORDER BY fecha_publicacion DESC, codigo DESC"
                        )
                        rows = cursor.fetchall()
            for item in rows:
                row = self.table.rowCount()
                self.table.insertRow(row)
                for column, value in enumerate((item[1], item[2], item[3], item[4] or "")):
                    cell = QTableWidgetItem(str(value))
                    if column == 0:
                        cell.setData(Qt.UserRole, item[0])
                    self.table.setItem(row, column, cell)
            self.filter_rows()
        except Exception as error:
            QMessageBox.warning(self, "No fue posible consultar versiones", str(error))

    def filter_rows(self):
        text = self.search.text().strip().lower()
        for row in range(self.table.rowCount()):
            values = " ".join(self.table.item(row, column).text().lower() for column in range(2))
            self.table.setRowHidden(row, bool(text) and text not in values)

    def accept_selection(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccione una versión", "Seleccione una versión publicada para continuar.")
            return
        self.selected_version = {
            "id": self.table.item(row, 0).data(Qt.UserRole),
            "codigo": self.table.item(row, 0).text(),
            "source": self.repository_source,
        }
        self.accept()


class RuleWorker(QObject):
    result = pyqtSignal(object)
    general_report = pyqtSignal(object, str)
    progress = pyqtSignal(int, int)
    fatal_error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, params, schema, prefix, r1_table, rules, general_report_path=None):
        super().__init__()
        self.params = params
        self.schema = schema
        self.prefix = prefix
        self.r1_table = r1_table
        self.rules = rules
        self.general_report_path = general_report_path

    def resolve_sql(self, sql):
        schema_prefix = self.schema.rstrip(".") + "."
        sql = sql.replace("{esquema}.{punto}", schema_prefix)
        sql = sql.replace("{esquema}{punto}.", schema_prefix)
        sql = sql.replace("{esquema}{punto}", schema_prefix)
        sql = sql.replace("{esquema}", schema_prefix).replace("{punto}", self.prefix)
        r1_markers = ("{esquema_r1}.{tabla_r1}", "{esquema_r1}{tabla_r1}")
        if any(marker in sql for marker in r1_markers):
            if not self.r1_table:
                raise ValueError("Esta regla requiere seleccionar una tabla R1 existente en public.")
            if not re.fullmatch(r"[A-Za-z0-9_]+", self.r1_table):
                raise ValueError("El nombre de la tabla R1 seleccionada no es válido.")
            for marker in r1_markers:
                sql = sql.replace(marker, f"public.{self.r1_table}")
        return sql

    def run(self):
        try:
            with psycopg2.connect(**self.params) as connection:
                for index, (category, rule_name, raw_sql, description) in enumerate(self.rules, 1):
                    try:
                        sql = self.resolve_sql(raw_sql)
                        with connection.cursor() as cursor:
                            cursor.execute(sql)
                            rows = cursor.fetchall() if cursor.description else []
                            fields = [column.name for column in cursor.description] if cursor.description else []
                        unique_fields = []
                        occurrences = {}
                        for name in fields:
                            occurrences[name] = occurrences.get(name, 0) + 1
                            unique_name = name if occurrences[name] == 1 else f"{name}__{occurrences[name]}"
                            while unique_name in unique_fields:
                                unique_name += '_'
                            unique_fields.append(unique_name)
                        detail_rows = [dict(zip(unique_fields, row)) for row in rows]
                        self.result.emit(RuleResult(rule_name, category, "Correcta", len(rows), rows=detail_rows, description=description,
                                                    criterion_hash=digest(sql), identity_safe=(
                                                        len(fields) == len(set(fields))
                                                        and not re.search(r"\b(?:row_number|rank|dense_rank)\s*\(", sql, re.IGNORECASE)
                                                    )))
                    except Exception as error:
                        connection.rollback()
                        detail = re.sub(r"\s+", " ", str(error)).strip()[:240]
                        self.result.emit(RuleResult(rule_name, category, "Error", "—", detail, description=description))
                    self.progress.emit(index, len(self.rules) + bool(self.general_report_path))
                if self.general_report_path:
                    try:
                        sql = self.resolve_sql(self.general_report_path)
                        with connection.cursor() as cursor:
                            cursor.execute(sql)
                            rows = cursor.fetchall() if cursor.description else []
                            fields = [column.name for column in cursor.description] if cursor.description else []
                        self.general_report.emit([dict(zip(fields, row)) for row in rows], "")
                    except Exception as error:
                        connection.rollback()
                        self.general_report.emit([], re.sub(r"\s+", " ", str(error)).strip()[:240])
                    self.progress.emit(len(self.rules) + 1, len(self.rules) + 1)
        except Exception as error:
            self.fatal_error.emit(str(error))
        finally:
            self.finished.emit()


class ControlCalidadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Validador Consistencia Lógica Alfanumérica")
        self.setWindowIcon(QIcon(str(PLUGIN_DIR / "icon.svg")))
        self.resize(1040, 700)
        self.results: list[RuleResult] = []
        self.review_cases = []
        self.review_imports = ReviewImports(self.review_cases)
        self.review_import_snapshot = {}
        self.detail_review_rows = {}
        self.detail_import_errors = {}
        self.review_dirty = False
        self.review_snapshot = []
        self.review_context = {}
        self.general_report_rows = []
        self.general_report_error = ""
        self.validation_context = "Ubicación territorial pendiente de identificar."
        self.selected_sql_version = None
        self.repository_rules = []
        self.thread = None
        self.worker = None
        self.category_checks = {}
        self.controls_running = False
        self._repository_password = None
        self.references_ready = False
        self._build()
        self.refresh_categories()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        self.setStyleSheet("QDialog { background: #F5F7F8; } QLabel { color: #575756; } "
                           "QLineEdit, QComboBox { color: #575756; background: white; border: 1px solid #3FA4F5; border-radius: 4px; padding: 5px; } "
                           "QComboBox QAbstractItemView { color: #575756; background: white; selection-color: white; selection-background-color: #068CBB; border: 1px solid #3FA4F5; } "
                           "QPushButton, QGroupBox QPushButton { background: #068CBB; color: white; border: none; border-radius: 5px; padding: 6px 10px; font-weight: 600; } "
                           "QPushButton:hover { background: #0468A3; } "
                           "QProgressBar { border: 1px solid #3FA4F5; border-radius: 5px; text-align: center; background: white; } "
                           "QProgressBar::chunk { background: #00C7CB; border-radius: 4px; }")

        def style_section(widget, color):
            widget.setStyleSheet(
                f"QGroupBox {{ background: white; border: 2px solid {color}; border-radius: 8px; margin-top: 12px; padding: 10px; font-weight: 700; color: #0468A3; }} "
                "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }"
            )

        heading = QLabel("Validador Consistencia Lógica Alfanumérica")
        heading.setStyleSheet("font-size: 22px; font-weight: 700; color: #0468A3;")
        layout.addWidget(heading)
        subtitle = QLabel("Modelo Interno de Levantamiento 1.0 y CICA · Validaciones alfanuméricas")
        subtitle.setStyleSheet("color: #52666a;")
        layout.addWidget(subtitle)

        splitter = QSplitter(Qt.Horizontal)
        self.main_splitter = splitter
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(6)
        connection = QGroupBox("1. Conexión PostgreSQL / PostGIS")
        style_section(connection, "#575756")
        connection.setStyleSheet(connection.styleSheet() +
            " QWidget { font-size: 12px; } QGroupBox { padding: 6px; } QLineEdit, QComboBox { padding: 3px; } "
            "QPushButton { padding: 4px 6px; }")
        form = QFormLayout(connection)
        form.setContentsMargins(6, 16, 6, 6)
        form.setSpacing(5)
        form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        form.setFormAlignment(Qt.AlignTop)
        self.model = QComboBox()
        self.model.addItems(MODELS)
        self.model.currentTextChanged.connect(self.reset_model_selection)
        self.model.activated.connect(self.reset_model_selection)
        self.connection_mode = QComboBox()
        self.connection_mode.addItems(["Conexión guardada en QGIS", "Conexión manual a PostgreSQL"])
        self.connection_mode.currentIndexChanged.connect(self.change_connection_mode)
        self.connection_stack = QStackedWidget()
        self.connection_stack.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.qgis_connection = QComboBox()
        self.qgis_connection.currentTextChanged.connect(self.describe_qgis_connection)
        qgis_page = QWidget()
        qgis_layout = QFormLayout(qgis_page)
        qgis_layout.setContentsMargins(0, 0, 0, 0)
        qgis_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        qgis_row = QHBoxLayout()
        refresh_qgis = QPushButton("Actualizar")
        refresh_qgis.clicked.connect(self.load_qgis_connections)
        qgis_row.addWidget(refresh_qgis)
        qgis_row.addWidget(self.qgis_connection, 1)
        qgis_layout.addRow("Conexión de QGIS", qgis_row)
        self.qgis_description = QLabel("Seleccione una conexión guardada en QGIS.")
        self.qgis_description.setWordWrap(True)
        self.qgis_description.setStyleSheet("color: #52666a;")
        qgis_layout.addRow("Base de datos", self.qgis_description)
        self.connection_stack.addWidget(qgis_page)
        manual_page = QWidget()
        manual_form = QFormLayout(manual_page)
        manual_form.setContentsMargins(0, 0, 0, 0)
        self.host = QLineEdit("localhost")
        self.port = QLineEdit("5432")
        self.database = QLineEdit()
        self.user = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        manual_form.addRow("Servidor", self.host)
        manual_form.addRow("Puerto", self.port)
        manual_form.addRow("Base de datos", self.database)
        manual_form.addRow("Usuario", self.user)
        manual_form.addRow("Contraseña", self.password)
        self.connection_stack.addWidget(manual_page)
        self.schema = QComboBox()
        self.schema.setEditable(False)
        form.addRow("Modelo", self.model)
        self.environment = QComboBox()
        self.environment.addItems(["Seleccione un ambiente…", "Validaciones del modelo", SNC_ENVIRONMENT])
        self.environment_label = QLabel("Ambiente")
        self.environment.currentTextChanged.connect(self.model_changed)
        form.addRow(self.environment_label, self.environment)
        self.sql_version_label = QLabel("Seleccione una versión de SQL")
        choose_sql_version = QPushButton("Buscar versión de sentencias…")
        self.choose_sql_version = choose_sql_version
        choose_sql_version.setEnabled(False)
        choose_sql_version.clicked.connect(self.open_sql_version_dialog)
        version_row = QVBoxLayout()
        version_row.setSpacing(4)
        version_row.addWidget(self.sql_version_label, 1)
        version_row.addWidget(choose_sql_version)
        form.addRow("Versión de SQL", version_row)
        self.ingestion_label = QLabel("Ingesta CICA")
        self.ingestion_button = QPushButton("Cargar insumos CICA…")
        self.ingestion_button.clicked.connect(self.open_ingestion)
        form.addRow(self.ingestion_label, self.ingestion_button)
        reference_button = QPushButton("Cargar en public R1 y R2…")
        reference_button.clicked.connect(self.open_references)
        form.addRow("Carga opcional", reference_button)
        self.published_r1 = QComboBox()
        self.published_r2 = QComboBox()
        self.refresh_references = QPushButton("Actualizar referencias publicadas")
        self.refresh_references.clicked.connect(self.load_public_references)
        self.published_r1.setEnabled(False)
        self.published_r2.setEnabled(False)
        self.refresh_references.setEnabled(False)
        form.addRow("Forma de conexión", self.connection_mode)
        form.addRow("", self.connection_stack)
        test = QPushButton("Listar Esquemas")
        test.clicked.connect(self.test_connection)
        self.schema_controls = QWidget()
        schema_form = QFormLayout(self.schema_controls)
        schema_form.setContentsMargins(0, 0, 0, 0)
        schema_form.setSpacing(5)
        schema_form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        schema_form.addRow(test)
        schema_form.addRow("Esquema a validar", self.schema)
        qgis_layout.addRow(self.schema_controls)
        form.addRow("R1 existente en public", self.published_r1)
        form.addRow("R2 existente en public", self.published_r2)
        form.addRow("", self.refresh_references)
        left_layout.addWidget(connection)
        info = QLabel("La contraseña se usa durante esta sesión y no se guarda. Las reglas se ejecutan en modo consulta y no alteran datos.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #52666a;")
        left_layout.addWidget(info)
        left_layout.addStretch()
        for combo in left.findChildren(QComboBox):
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(10)
            combo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            combo.setMinimumWidth(100)
        for label in left.findChildren(QLabel):
            label.setWordWrap(True)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setMinimumWidth(250)
        left_scroll.setWidget(left)
        splitter.addWidget(left_scroll)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        group = QGroupBox("2. Controles a ejecutar")
        style_section(group, "#00C7CB")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(8, 10, 8, 7)
        group_layout.setSpacing(5)
        control_row = QHBoxLayout()
        all_button = QPushButton("Seleccionar todos")
        all_button.clicked.connect(self.select_all_categories)
        control_row.addWidget(all_button)
        self.category_summary = QLabel()
        self.category_summary.setWordWrap(True)
        self.category_summary.setStyleSheet("color: #575756;")
        control_row.addWidget(self.category_summary)
        control_row.addStretch()
        group_layout.addLayout(control_row)
        self.category_cards = QGridLayout()
        self.category_cards.setHorizontalSpacing(6)
        self.category_cards.setVerticalSpacing(6)
        group_layout.addLayout(self.category_cards)
        right_layout.addWidget(group)
        hint = QLabel("Los grupos seleccionados se ejecutan sin modificar los datos de origen.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #52666a;")
        right_layout.addWidget(hint)

        result_box = QGroupBox("3. Resultados de la ejecución")
        style_section(result_box, "#3FA4F5")
        result_layout = QVBoxLayout(result_box)
        self.summary = QLabel("Aún no se han ejecutado controles.")
        self.summary.setWordWrap(True)
        result_layout.addWidget(self.summary)
        self.location_summary = QLabel("Ubicación territorial: se identificará al ejecutar los controles.")
        self.location_summary.setWordWrap(True)
        self.location_summary.setStyleSheet("color: #0468A3; font-weight: 600; background: #E2F7F8; border-radius: 4px; padding: 5px;")
        result_layout.addWidget(self.location_summary)
        self.table = QTableWidget(0, len(STAT_HEADERS))
        self.table.setHorizontalHeaderLabels([
            header.replace('Reglas ejecutadas', 'Reglas\nejecutadas').replace('Errores técnicos', 'Errores\ntécnicos')
            for header in STAT_HEADERS
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("QTableWidget { background: white; gridline-color: #D7EAF7; border: 1px solid #3FA4F5; } "
                                 "QHeaderView::section { background: #068CBB; color: white; border: none; padding: 4px; font-size: 12px; font-weight: 700; } "
                                 "QTableWidget::item:selected { background: #BFEAF0; color: #575756; }")
        self.table.setMinimumHeight(160)
        result_layout.addWidget(self.table)
        review_actions = QHBoxLayout()
        self.review_save_button = QPushButton("Guardar revisión en Excel")
        self.review_save_button.clicked.connect(self.save_review_excel)
        self.review_recover_button = QPushButton("Cargar revisión consolidada")
        self.review_recover_button.clicked.connect(self.recover_review)
        for button in (self.review_save_button, self.review_recover_button):
            button.setEnabled(False)
            review_actions.addWidget(button)
        result_layout.addLayout(review_actions)
        detail_group = QGroupBox("Detalles de revisión — cargar o liberar por componente")
        detail_group_layout = QVBoxLayout(detail_group)
        detail_note = QLabel("Los archivos no quedan abiertos. Liberar retira su revisión importada; después puede editar el Excel y volver a cargarlo.")
        detail_note.setWordWrap(True)
        detail_group_layout.addWidget(detail_note)
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setMaximumHeight(160)
        detail_content = QWidget()
        self.detail_review_layout = QGridLayout(detail_content)
        detail_scroll.setWidget(detail_content)
        detail_group_layout.addWidget(detail_scroll)
        result_layout.addWidget(detail_group)
        right_layout.addWidget(result_box, 1)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 740])

        controls = QHBoxLayout()
        self.progress = QProgressBar(self)
        self.progress.setVisible(False)
        self.progress.setMinimumWidth(230)
        controls.addWidget(self.progress)
        self.status = QLabel("Configure la conexión y seleccione los controles.")
        controls.addWidget(self.status, 1)
        self.export_button = QPushButton("Generar reporte detallado")
        self.export_button.clicked.connect(self.export_excel)
        self.run_button = QPushButton("Ejecutar controles")
        self.run_button.setEnabled(False)
        self.run_button.setStyleSheet("background: #0468A3; color: white; font-weight: 700; padding: 8px 14px;")
        self.run_button.clicked.connect(self.run_rules)
        controls.addWidget(self.export_button)
        controls.addWidget(self.run_button)
        layout.addLayout(controls)
        self.load_qgis_connections()
        self.update_ingestion_button()
        self.resize_connection_stack()

    def resize_connection_stack(self):
        page = self.connection_stack.currentWidget()
        if page is not None:
            page.layout().activate()
            self.connection_stack.setFixedHeight(page.sizeHint().height() + 4)

    def update_ingestion_button(self, *_):
        supports_snc = self.model.currentText() in SNC_REPOSITORY_TABLES
        self.environment.setVisible(supports_snc)
        self.environment_label.setVisible(supports_snc)
        if not supports_snc:
            self.environment.blockSignals(True)
            self.environment.setCurrentIndex(0)
            self.environment.blockSignals(False)
        visible = self.model.currentText() == "CICA"
        self.ingestion_label.setVisible(visible)
        self.ingestion_button.setVisible(visible)

    def reset_model_selection(self, *_):
        self.environment.blockSignals(True)
        self.environment.setCurrentIndex(0)
        self.environment.blockSignals(False)
        self.update_ingestion_button()
        self.choose_sql_version.setEnabled(False)
        self.clear_repository_rules()

    def model_changed(self, *_):
        self.clear_repository_rules()
        self.choose_sql_version.setEnabled(self.environment.currentIndex() > 0)
        if self.environment.currentIndex() > 0:
            self.open_sql_version_dialog()

    def repository_connection_params(self):
        params = dict(REPOSITORY_CONNECTION)
        if params.get("password"):
            return params
        if self._repository_password is None:
            password, accepted = QInputDialog.getText(
                self, "Acceso al repositorio de sentencias",
                "Contraseña del repositorio de sentencias (solo para esta sesión):",
                QLineEdit.Password,
            )
            if not accepted or not password:
                self.status.setText("Ejecución bloqueada: falta autenticar el acceso al repositorio de sentencias.")
                return None
            self._repository_password = password
        params["password"] = self._repository_password
        return params

    def repository_source(self, params):
        if self.environment.currentText() == SNC_ENVIRONMENT:
            table = SNC_REPOSITORY_TABLES[self.model.currentText()]
            with psycopg2.connect(**params, connect_timeout=8) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT to_regclass(%s)", (f"public.{table}",))
                    if not cursor.fetchone()[0]:
                        raise ValueError(f"La tabla public.{table} aún no está disponible para el cargue SNC.")
                    cursor.execute("SELECT has_table_privilege(current_user, %s, 'SELECT')", (f"public.{table}",))
                    if not cursor.fetchone()[0]:
                        raise ValueError(f"Se requiere permiso SELECT sobre public.{table}.")
            return {"kind": "tables", "schema": "public", "tables": [table], "label": f"public.{table}", "snc": True}
        with psycopg2.connect(**params, connect_timeout=8) as connection:
            with connection.cursor() as cursor:
                tables = []
                for table in SQL_REPOSITORY_TABLES[self.model.currentText()]:
                    cursor.execute("SELECT to_regclass(%s), has_table_privilege(current_user, %s, 'SELECT')", (f"public.{table}", f"public.{table}"))
                    exists, readable = cursor.fetchone()
                    if exists and readable:
                        tables.append(table)
                if tables:
                    return {"kind": "tables", "schema": "public", "tables": tables, "label": "public." + ", public.".join(tables)}
        candidates = SQL_REPOSITORIES[self.model.currentText()]
        with psycopg2.connect(**params, connect_timeout=8) as connection:
            with connection.cursor() as cursor:
                for schema in candidates:
                    cursor.execute("SELECT to_regnamespace(%s)", (schema,))
                    if cursor.fetchone()[0]:
                        return {"kind": "schema", "schema": schema, "label": f"{schema}.reglas"}
        raise ValueError("No se encontró el repositorio centralizado de SQL para el modelo seleccionado.")

    def clear_repository_rules(self):
        self.selected_sql_version = None
        self.repository_rules = []
        self.sql_version_label.setText("Seleccione una versión de SQL")
        self.refresh_categories()
        self.status.setText("Ejecución bloqueada: seleccione una versión con controles activos del repositorio SQL.")

    def update_run_availability(self):
        selected = {name for name, card in self.category_checks.items() if card.isChecked()}
        ready = bool(self.selected_sql_version) and any(
            item["type"] == "CONTROL" and item["component"] in selected
            and item["sql"] and item["sql"].strip()
            for item in self.repository_rules
        )
        self.run_button.setEnabled(ready and not self.controls_running)
        self.run_button.setToolTip("" if ready else "Cargue una versión del repositorio con controles activos y seleccione al menos un grupo.")

    def open_sql_version_dialog(self):
        self.clear_repository_rules()
        if self.environment.currentIndex() == 0:
            QMessageBox.information(self, "Seleccione un ambiente", "Seleccione el ambiente antes de buscar una versión de SQL.")
            return
        if psycopg2 is None:
            QMessageBox.warning(self, "Dependencia faltante", "No se puede consultar el repositorio SQL sin psycopg2.")
            return
        try:
            params = self.repository_connection_params()
            if params is None:
                return
            source = self.repository_source(params)
        except Exception as error:
            if getattr(error, "pgcode", None) in ("28P01", "28000"):
                self._repository_password = None
            QMessageBox.information(self, "No fue posible conectar al repositorio", str(error))
            return
        dialog = SqlVersionDialog(self, params, source)
        if dialog.exec() != QDialog.Accepted or not dialog.selected_version:
            return
        version = dialog.selected_version
        try:
            with psycopg2.connect(**params, connect_timeout=8) as connection:
                with connection.cursor() as cursor:
                    if source["kind"] == "tables":
                        table = version["id"]["table"]
                        cursor.execute(
                            f"SELECT componente, codigo_regla, tipo, sentencia_sql, COALESCE(descripcion_regla, '') FROM public.{table} AS regla "
                            "WHERE version = %s AND activa AND ("
                            f"SELECT cabecera.version_publicada FROM public.{table} AS cabecera "
                            "WHERE cabecera.version = regla.version "
                            "ORDER BY cabecera.orden NULLS LAST, cabecera.componente, cabecera.codigo_regla LIMIT 1"
                            ") IS TRUE ORDER BY componente, orden, codigo_regla",
                            (version["id"]["version"],),
                        )
                    else:
                        cursor.execute(
                            f"SELECT componente, codigo_regla, tipo, sentencia_sql, COALESCE(descripcion, '') FROM {source['schema']}.reglas "
                            "WHERE version_id = %s AND activa ORDER BY componente, orden, codigo_regla",
                            (version["id"],),
                        )
                    self.repository_rules = [
                        {"component": SNC_CATEGORY if source.get("snc") and row[2] == "CONTROL" else row[0],
                         "source_component": row[0], "rule": row[1], "type": row[2], "sql": row[3], "description": row[4]}
                        for row in cursor.fetchall()
                    ]
            self.selected_sql_version = dict(version, source=source)
            self.sql_version_label.setText(f"{version['codigo']} · {len(self.repository_rules)} sentencias")
            self.refresh_categories()
            if any(item["type"] == "CONTROL" and item["sql"] and item["sql"].strip() for item in self.repository_rules):
                self.status.setText(f"Versión SQL seleccionada: {version['codigo']}.")
            else:
                self.status.setText("Ejecución bloqueada: la versión seleccionada no contiene controles activos.")
        except Exception as error:
            self.clear_repository_rules()
            QMessageBox.warning(self, "No fue posible cargar reglas", str(error))

    def open_ingestion(self):
        dialog = CicaIngestionDialog(self)
        dialog.exec()

    def open_references(self):
        dialog = ReferenceDialog(self, self.connection_params)
        dialog.exec()
        self.load_public_references()

    def load_public_references(self):
        if not self.references_ready:
            return
        if psycopg2 is None:
            return
        try:
            with psycopg2.connect(**self.connection_params(), connect_timeout=8) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND lower(table_name) LIKE 'r1%' ORDER BY table_name")
                    r1 = [item[0] for item in cursor.fetchall()]
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND lower(table_name) LIKE 'r2%' ORDER BY table_name")
                    r2 = [item[0] for item in cursor.fetchall()]
            self.published_r1.clear(); self.published_r1.addItems(r1)
            self.published_r2.clear(); self.published_r2.addItems(r2)
            self.status.setText(f"Referencias disponibles en public: {len(r1)} R1 y {len(r2)} R2.")
        except Exception as error:
            QMessageBox.warning(self, "No fue posible consultar public", str(error))


    def change_connection_mode(self, index):
        self.connection_stack.setCurrentIndex(index)
        destination = self.connection_stack.currentWidget()
        if self.schema_controls.parentWidget() is not destination:
            previous_layout = self.schema_controls.parentWidget().layout()
            previous_row, _ = previous_layout.getWidgetPosition(self.schema_controls)
            previous_layout.takeRow(previous_row)
            destination.layout().addRow(self.schema_controls)
        self.resize_connection_stack()
        self.schema.clear()
        self.status.setText("Pulse Listar Esquemas para cargar los esquemas disponibles.")

    def load_qgis_connections(self):
        settings = QgsSettings()
        settings.beginGroup("PostgreSQL/connections")
        names = sorted(settings.childGroups())
        settings.endGroup()
        current = self.qgis_connection.currentText()
        self.qgis_connection.blockSignals(True)
        self.qgis_connection.clear()
        self.qgis_connection.addItems(names)
        if current in names:
            self.qgis_connection.setCurrentText(current)
        self.qgis_connection.blockSignals(False)
        self.describe_qgis_connection(self.qgis_connection.currentText())

    def describe_qgis_connection(self, name):
        if not name:
            self.qgis_description.setText("No se encontraron conexiones PostgreSQL guardadas en este perfil de QGIS.")
            return
        settings = QgsSettings()
        group = f"PostgreSQL/connections/{name}"
        host = settings.value(f"{group}/host", "")
        port = settings.value(f"{group}/port", "5432")
        database = settings.value(f"{group}/database", "")
        self.qgis_description.setText(f"{host}:{port} · {database}")

    def qgis_connection_params(self):
        name = self.qgis_connection.currentText()
        if not name:
            raise ValueError("Seleccione una conexión PostgreSQL guardada en QGIS.")
        settings = QgsSettings()
        group = f"PostgreSQL/connections/{name}"
        params = {
            "host": settings.value(f"{group}/host", ""),
            "port": settings.value(f"{group}/port", "5432"),
            "dbname": settings.value(f"{group}/database", ""),
            "user": settings.value(f"{group}/username", ""),
            "password": settings.value(f"{group}/password", ""),
        }
        authcfg = settings.value(f"{group}/authcfg", "")
        if authcfg:
            auth_config = QgsAuthMethodConfig()
            if QgsApplication.authManager().loadAuthenticationConfig(authcfg, auth_config, True):
                params["user"] = auth_config.config("username") or params["user"]
                params["password"] = auth_config.config("password") or params["password"]
        return params

    def refresh_categories(self, *_):
        if not hasattr(self, "category_cards"):
            return
        while self.category_cards.count():
            item = self.category_cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.category_checks.clear()
        if self.repository_rules:
            counts = defaultdict(int)
            for item in self.repository_rules:
                if item["type"] == "CONTROL" and item["sql"] and item["sql"].strip():
                    counts[item["component"]] += 1
            self.populate_category_cards(sorted(counts.items()))
            return
        self.populate_category_cards([])

    def populate_category_cards(self, categories):
        categories = list(categories)
        if not self.selected_sql_version and self.model.currentText() in SNC_REPOSITORY_TABLES and not any(name == SNC_CATEGORY for name, _ in categories):
            categories.append((SNC_CATEGORY, 0))
        for index, (category_name, count) in enumerate(categories):
            card = QPushButton()
            card.setObjectName("categoryCard")
            card.setCheckable(True)
            optional_snc = category_name == SNC_CATEGORY
            snc_selected = (
                optional_snc and count > 0 and bool(self.selected_sql_version)
            )
            card.setChecked(not optional_snc or snc_selected)
            card.setEnabled(not optional_snc or count > 0)
            if optional_snc and not count:
                card.setToolTip("Pendiente incorporar las reglas SQL de cargue a SNC para este modelo y ambiente.")
            card.setIconSize(QSize(14, 14))
            card.setLayoutDirection(Qt.RightToLeft)
            card.setMinimumHeight(30)
            card.setStyleSheet(
                "QPushButton#categoryCard { background: #F7F9FA; color: #9AA3A8; border: 1px solid #D7E0E5; "
                "border-radius: 5px; text-align: left; padding: 3px 7px; font-weight: 600; } "
                "QPushButton#categoryCard:hover { background: #E2F7F8; color: #0468A3; border: 2px solid #3FA4F5; } "
                "QPushButton#categoryCard:checked { background: #0468A3; color: white; border: 2px solid #00C7CB; }"
            )
            self.update_category_card(card, category_name, count, card.isChecked())
            card.toggled.connect(lambda checked, button=card, name=category_name, rules=count: self.update_category_card(button, name, rules, checked))
            card.toggled.connect(self.update_category_summary)
            self.category_checks[category_name] = card
            self.category_cards.addWidget(card, index // 3, index % 3)
        self.update_category_summary()

    @staticmethod
    def update_category_card(card, name, rules, checked):
        icon_name = "selected.svg" if checked else "unselected.svg"
        card.setIcon(QIcon(str(PLUGIN_DIR / "resources" / "icons" / icon_name)))
        card.setText("+ Cargue SNC" if name == SNC_CATEGORY else f"{name} · {rules} reglas")

    def select_all_categories(self):
        for name, action in self.category_checks.items():
            if name != SNC_CATEGORY and action.isEnabled():
                action.setChecked(True)
        self.update_category_summary()

    def update_category_summary(self, *_):
        selected = [name for name, action in self.category_checks.items() if action.isChecked()]
        if self.repository_rules:
            count = sum(1 for item in self.repository_rules if item["type"] == "CONTROL" and item["component"] in selected and item["sql"] and item["sql"].strip())
        else:
            count = sum(len(list((SQL_ROOT / MODELS[self.model.currentText()] / name).glob("*.sql"))) for name in selected)
        self.category_summary.setText(f"{len(selected)} grupos seleccionados · {count} reglas a ejecutar")
        self.update_run_availability()

    def connection_params(self):
        if self.connection_mode.currentIndex() == 0:
            return self.qgis_connection_params()
        return {"host": self.host.text().strip(), "port": self.port.text().strip(), "dbname": self.database.text().strip(), "user": self.user.text().strip(), "password": self.password.text()}

    def resolve_validation_context(self, params, schema):
        """Relaciona los cinco primeros dígitos de ILC_Predio con el DIVIPOLA interno."""
        if not DIVIPOLA_FILE.exists():
            return "Ubicación territorial no disponible: falta la referencia DIVIPOLA del plugin."
        if not re.fullmatch(r"[A-Za-z0-9_]+", schema):
            return "Ubicación territorial no disponible: el nombre del esquema no es válido."
        try:
            workbook = load_workbook(DIVIPOLA_FILE, read_only=True, data_only=True)
            sheet = workbook.active
            divipola = {
                str(code).strip().zfill(5): (str(department).strip(), str(municipality).strip())
                for code, department, municipality in sheet.iter_rows(min_row=2, values_only=True)
                if code not in (None, "") and department not in (None, "") and municipality not in (None, "")
            }
            with psycopg2.connect(**params, connect_timeout=8) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema = %s AND table_name = 'ilc_predio' "
                        "AND column_name IN ('numero_predial', 'numero_predial_nacional')",
                        (schema,),
                    )
                    available = {row[0] for row in cursor.fetchall()}
                    field = "numero_predial" if "numero_predial" in available else "numero_predial_nacional"
                    if field not in available:
                        return "Ubicación territorial no disponible: ILC_Predio no tiene un campo de número predial reconocido."
                    cursor.execute(
                        f"SELECT DISTINCT left({field}::text, 5) FROM {schema}.ilc_predio "
                        f"WHERE {field} IS NOT NULL AND length({field}::text) >= 5 ORDER BY 1"
                    )
                    codes = [str(row[0]).zfill(5) for row in cursor.fetchall()]
            matches = [(code, *divipola[code]) for code in codes if code in divipola]
            if not codes:
                return "Ubicación territorial no identificada: ILC_Predio no contiene números prediales válidos."
            if not matches:
                return "Ubicación territorial no identificada: los códigos DIVIPOLA no están en la referencia interna."
            labels = [f"{department} · {municipality} ({code})" for code, department, municipality in matches]
            visible = labels[:4]
            suffix = f" · y {len(labels) - len(visible)} más" if len(labels) > len(visible) else ""
            return "Ubicación territorial validada: " + "; ".join(visible) + suffix
        except Exception as error:
            return "Ubicación territorial no disponible: " + re.sub(r"\s+", " ", str(error)).strip()[:160]

    def test_connection(self):
        if psycopg2 is None:
            QMessageBox.critical(self, "Dependencia faltante", "El QGIS instalado no incluye psycopg2. Instale psycopg2-binary en el Python de QGIS.")
            return
        try:
            with psycopg2.connect(**self.connection_params(), connect_timeout=8) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    cursor.execute("SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname <> 'information_schema' ORDER BY nspname")
                    schemas = [row[0] for row in cursor.fetchall()]
            self.schema.clear()
            self.schema.addItems(schemas)
            if "public" in schemas:
                self.schema.setCurrentText("public")
            self.status.setText("Conexión exitosa: " + version.split(",")[0])
            self.references_ready = True
            self.published_r1.setEnabled(True)
            self.published_r2.setEnabled(True)
            self.refresh_references.setEnabled(True)
            self.load_public_references()
        except Exception as error:
            QMessageBox.critical(self, "No fue posible conectar", str(error))

    def run_rules(self):
        self.update_run_availability()
        if not self.run_button.isEnabled():
            QMessageBox.warning(self, "Controles no disponibles", "Cargue una versión del repositorio SQL con controles activos y seleccione los grupos a ejecutar.")
            return
        if psycopg2 is None:
            QMessageBox.critical(self, "Dependencia faltante", "El QGIS instalado no incluye psycopg2.")
            return
        selected = [name for name, check in self.category_checks.items() if check.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Seleccione controles", "Seleccione al menos una categoría de reglas.")
            return
        rules = [
            (item["component"], item["rule"], item["sql"], item.get("description", ""))
            for item in self.repository_rules
            if item["type"] == "CONTROL" and item["component"] in selected
            and item["sql"] and item["sql"].strip()
        ]
        general_report_path = next(
            (item["sql"] for item in self.repository_rules if item["type"] == "REPORTE_GENERAL"), None
        )
        if not rules:
            QMessageBox.critical(self, "Reglas no encontradas", "No hay reglas SQL en la selección actual.")
            return
        schema = self.schema.currentText().strip()
        if not schema:
            QMessageBox.warning(self, "Seleccione un esquema", "Pulse Listar Esquemas y seleccione el esquema que desea validar.")
            return
        try:
            params = self.connection_params()
        except Exception as error:
            QMessageBox.warning(self, "Conexión incompleta", str(error))
            return
        if not self.commit_review_editor() or not self.confirm_review_changes():
            return
        self.results.clear()
        self.review_cases = []
        self.review_imports = ReviewImports(self.review_cases)
        self.review_import_snapshot = {}
        self.detail_import_errors = {}
        self.refresh_detail_review_controls()
        self.review_snapshot = []
        self.review_dirty = False
        self.review_context = {
            "model": self.model.currentText(), "environment": self.environment.currentText(),
            "host": params.get("host", ""), "port": str(params.get("port", "5432")),
            "database": params.get("dbname", ""), "schema": schema,
            "reference_r1": self.published_r1.currentText(),
            "repository": self.selected_sql_version.get("source", {}).get("label", ""),
        }
        for button in (self.review_save_button, self.review_recover_button):
            button.setEnabled(False)
        self.table.setRowCount(0)
        self.general_report_rows = []
        self.general_report_error = ""
        self.validation_context = self.resolve_validation_context(params, schema)
        self.location_summary.setText(self.validation_context)
        self.progress.setRange(0, len(rules) + bool(general_report_path))
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.status.setText(f"Ejecutando {len(rules)} reglas y reporte general…")
        self.controls_running = True
        self.run_button.setEnabled(False)
        self.thread = QThread(self)
        self.worker = RuleWorker(params, schema, "", self.published_r1.currentText(), rules, general_report_path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.add_result)
        self.worker.general_report.connect(self.add_general_report)
        self.worker.progress.connect(self.set_progress)
        self.worker.fatal_error.connect(lambda text: QMessageBox.critical(self, "No fue posible ejecutar", text))
        self.worker.finished.connect(self.finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def add_result(self, result):
        self.results.append(result)
        self.review_cases.extend(build_cases([result], self.review_context))

    def add_general_report(self, rows, error):
        self.general_report_rows = rows
        self.general_report_error = error

    def set_progress(self, current, total):
        self.progress.setRange(0, total)
        self.progress.setValue(current)
        self.status.setText(f"Ejecutando regla {current} de {total}…")

    def finished(self):
        self.controls_running = False
        self.update_run_availability()
        self.progress.setValue(self.progress.maximum())
        self.status.setText("Ejecución terminada.")
        self.review_imports = ReviewImports(self.review_cases)
        self.detail_import_errors = {}
        self.review_import_snapshot = self.review_imports.snapshot()
        self.refresh_detail_review_controls()
        self.review_snapshot = [case.tracking() + case.exception_tracking() for case in self.review_cases]
        self.review_save_button.setEnabled(bool(self.results))
        self.review_recover_button.setEnabled(bool(self.review_cases))


    def commit_review_editor(self):
        # Reviews are edited in Excel; no record-review window is created.
        return True

    def save_review_excel(self):
        if self.controls_running or not self.results or not self.commit_review_editor():
            return False
        path, _ = QFileDialog.getSaveFileName(self, "Guardar revisión en Excel", "revision_catastral.xlsx", "Excel (*.xlsx)")
        if not path:
            return False
        if not path.lower().endswith('.xlsx'):
            path += '.xlsx'
        try:
            save_review(path, self.review_cases, self.results, self.general_report_rows)
        except Exception as error:
            QMessageBox.warning(self, "No se guardó la revisión", str(error))
            return False
        self.review_dirty = False
        self.review_snapshot = [case.tracking() + case.exception_tracking() for case in self.review_cases]
        self.review_import_snapshot = self.review_imports.snapshot()
        self.status.setText("Revisión completa guardada; los filtros no excluyen registros.")
        return True

    def refresh_review_statistics(self):
        groups, totals = review_statistics(self.results, self.review_cases)
        self.table.setRowCount(0)
        for component, values in sorted(groups.items()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate(statistics_row(component, values)):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.summary.setText(
            f"{totals['rules']} reglas ejecutadas · {totals['findings']} hallazgos · "
            f"{totals['dt'] + totals['operator']} excepciones · "
            f"{totals['pending']} errores · {totals['errors']} errores técnicos"
        )

    def refresh_detail_review_controls(self):
        self.refresh_review_statistics()
        components = sorted({case.component for case in self.review_cases})
        if set(components) != set(self.detail_review_rows):
            while self.detail_review_layout.count():
                item = self.detail_review_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.detail_review_rows = {}
            for row, component in enumerate(components):
                name = QLabel(component)
                load = QPushButton("Cargar detalle")
                release = QPushButton("Liberar")
                state = QLabel("No cargado")
                state.setWordWrap(True)
                load.clicked.connect(lambda checked=False, c=component: self.recover_detail(c))
                release.clicked.connect(lambda checked=False, c=component: self.release_detail(c))
                for column, widget in enumerate((name, load, release, state)):
                    self.detail_review_layout.addWidget(widget, row, column)
                self.detail_review_rows[component] = (load, release, state)
        for component, (load, release, state) in self.detail_review_rows.items():
            source = self.review_imports.sources.get(component)
            load.setEnabled(not self.controls_running)
            release.setEnabled(bool(source) and not self.controls_running)
            load.setText("Recargar detalle" if source else "Cargar detalle")
            if source:
                counts = source['counts']
                warnings = sum(counts[name] for name in ('sin_correspondencia', 'ambiguas', 'conflictos', 'excepciones_invalidas', 'estados_invalidos', 'datos_invalidos', 'operador_bloqueado'))
                label = ('Cargado con observaciones' if warnings else 'Cargado') if counts['coincidencias'] else 'Sin coincidencias'
                state.setText(f"{label}: {Path(source['path']).name} · {counts['incorporadas']} incorporadas · {counts['conflictos']} conflictos")
                state.setToolTip(source['path'])
                color = '#087F23' if counts['coincidencias'] and not warnings else '#A05A00'
                state.setStyleSheet(f'color: {color}; font-weight: 600;')
            else:
                state.setText('No cargado')
                state.setToolTip('')
                state.setStyleSheet('color: #575756;')
            if component in self.detail_import_errors:
                state.setText('Error de carga — ' + state.text())
                state.setStyleSheet('color: #B00020; font-weight: 600;')
                state.setToolTip(self.detail_import_errors[component])

    def recovery_message(self, counts):
        return (
            f"Revisiones incorporadas: {counts['incorporadas']}\n"
            f"Sin correspondencia: {counts['sin_correspondencia']}\n"
            f"Correspondencias ambiguas: {counts['ambiguas']}\n"
            f"Seguimientos actuales conservados por conflicto: {counts['conflictos']}\n"
            f"Excepciones sin observación descartadas: {counts['excepciones_invalidas']}\n"
            f"Campos de operador descartados por Excepción DT: {counts['operador_bloqueado']}\n"
            f"Datos alterados o no recuperables: {counts['datos_invalidos']}\n"
            f"Identidad insuficiente: {counts['identidad_insuficiente']}\n"
            f"Datos o identidad alterados: {counts['identidad_alterada']}"
        )

    def recover_detail(self, component):
        if self.controls_running or not self.review_cases:
            return
        path, _ = QFileDialog.getOpenFileName(self, f"Cargar detalle: {component}", "", "Excel de revisión (*.xlsx)")
        if not path:
            return
        try:
            records = load_review(path)
            previous = [case.tracking() + case.exception_tracking() for case in self.review_cases]
            counts = self.review_imports.load(component, path, records)
        except Exception as error:
            self.detail_import_errors[component] = str(error)
            self.refresh_detail_review_controls()
            QMessageBox.warning(self, "No se cargó el detalle", str(error))
            return
        self.review_dirty = self.review_dirty or previous != [case.tracking() + case.exception_tracking() for case in self.review_cases]
        self.detail_import_errors.pop(component, None)
        self.refresh_detail_review_controls()
        QMessageBox.information(self, f"Detalle {component}", self.recovery_message(counts))

    def release_detail(self, component):
        if self.controls_running or component not in self.review_imports.sources:
            return
        answer = QMessageBox.question(self, "Liberar detalle", f"Se retirará de la ejecución actual la revisión importada de {component}. El Excel no se modifica. ¿Continuar?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        counts = self.review_imports.release(component)
        self.detail_import_errors.pop(component, None)
        self.review_dirty = self.review_dirty or bool(counts['retiradas'])
        self.refresh_detail_review_controls()
        self.status.setText(f"Detalle {component} liberado. Puede editar el archivo y volver a cargarlo. {counts['conservadas']} ediciones posteriores conservadas.")

    def recover_review(self):
        if self.controls_running or not self.review_cases:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Cargar revisión consolidada", "", "Excel de revisión (*.xlsx)")
        if not path:
            return
        try:
            records = load_review(path)
            groups = sorted({record.component for record in records if record.component})
            existing = [component for component in groups if component in self.review_imports.sources]
            if existing:
                raise ValueError('Ya hay detalles cargados: ' + ', '.join(existing) + '. Use Recargar detalle o Liberar para reemplazarlos explícitamente.')
            supported = {case.component for case in self.review_cases}
            messages = []
            for component in groups:
                if component not in supported:
                    messages.append(component + ': sin resultados en la ejecución actual.')
                    continue
                subset = [record for record in records if record.component == component]
                counts = self.review_imports.load(component, path, subset)
                self.review_dirty = self.review_dirty or bool(counts['incorporadas'])
                self.detail_import_errors.pop(component, None)
                messages.append(component + ':\n' + self.recovery_message(counts))
            if not groups:
                raise ValueError('El archivo no identifica los componentes de revisión.')
        except Exception as error:
            QMessageBox.warning(self, "No se recuperó la revisión", str(error))
            return
        self.refresh_detail_review_controls()
        QMessageBox.information(self, "Recuperación de revisión", '\n\n'.join(messages))

    def confirm_review_changes(self):
        if not self.review_dirty:
            return True
        choice = QMessageBox.question(
            self, "Revisión sin guardar", "Hay modificaciones de revisión sin guardar. ¿Desea guardarlas en Excel?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel,
        )
        if choice == QMessageBox.Save:
            return self.save_review_excel()
        if choice == QMessageBox.Discard:
            for case, tracking in zip(self.review_cases, self.review_snapshot):
                for name, value in zip(REVIEW_FIELDS + EXCEPTION_FIELDS, tracking):
                    setattr(case, name, value)
            self.review_imports.restore_snapshot(self.review_import_snapshot)
            self.refresh_detail_review_controls()
            self.review_dirty = False
            return True
        return False

    def closeEvent(self, event):
        if self.controls_running:
            QMessageBox.information(self, "Validación en curso", "Espere a que termine la ejecución antes de cerrar.")
            event.ignore()
        elif self.commit_review_editor() and self.confirm_review_changes():
            event.accept()
        else:
            event.ignore()

    def reject(self):
        self.close()

    def export_excel(self):
        if not self.commit_review_editor():
            return
        if not self.results:
            QMessageBox.information(self, "Sin resultados", "Ejecute controles antes de exportar un reporte.")
            return
        directory = QFileDialog.getExistingDirectory(self, "Seleccione la carpeta para guardar el reporte detallado")
        if not directory:
            return
        rule_sheet_count = len({(result.category, result.rule) for result in self.results if result.rows})
        package_count = len({result.category for result in self.results if result.rows})
        report_total = max(len(self.results) + rule_sheet_count + package_count + 3, 1)
        report_step = 0
        self.progress.setRange(0, report_total)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.export_button.setEnabled(False)
        self.status.setText("Preparando reporte detallado…")
        QApplication.processEvents()

        def advance_report(message):
            nonlocal report_step
            report_step += 1
            self.progress.setValue(min(report_step, report_total))
            self.status.setText(message)
            QApplication.processEvents()

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(Path(directory) / f"resumen_control_calidad_{stamp}.xlsx")
        book = Workbook()
        summary = book.active
        summary.title = "Resumen ejecutivo"
        context = book.create_sheet("Contexto de validación", 0)
        context.append(["Ubicación territorial validada"])
        context.append([self.validation_context])
        summary.append(STAT_HEADERS)
        groups, totals = review_statistics(self.results, self.review_cases)
        for result in self.results:
            advance_report("Organizando resumen ejecutivo…")
        for category, values in sorted(groups.items()):
            summary.append(statistics_row(category, values))
        summary.append(statistics_row('TOTAL', totals))
        general = book.create_sheet("Reporte general")
        general.append(["ID", "Ítem evaluado", "Cantidad", "Reglas asociadas"])
        if self.general_report_rows:
            for item in self.general_report_rows:
                values = {str(key).lower(): value for key, value in item.items()}
                general.append([
                    values.get("id", ""), values.get("descripcion", ""), values.get("cantidad", ""),
                    values.get("reglas_validacion_afectadas", values.get("reglas_validacion_afectadas", "")),
                ])
        else:
            general.append(["", "No fue posible generar el reporte general", "", self.general_report_error or "No se recibieron resultados."])
        detail = book.create_sheet("Detalle de errores")
        detail.append(["Componente", "Regla incumplida", "Hallazgos", "Hoja de detalle"])
        error_rows = []
        review_by_row = {
            id(row): case for row, case in zip(
                [row for result in self.results for row in result.rows or []], self.review_cases
            )
        }
        rows_by_rule = defaultdict(list)
        rule_descriptions = {}
        for result in self.results:
            rule_descriptions[(result.category, result.rule)] = result.description or ""
            for row in result.rows or []:
                predio = self.predio_from_row(row)
                error_rows.append((predio, result.category, result.rule, row))
                rows_by_rule[(result.category, result.rule)].append((predio, row))
        green = PatternFill("solid", fgColor="068CBB")
        navy = green
        red = green
        soft_blue = PatternFill("solid", fgColor="EAF3F8")
        soft_gray = PatternFill("solid", fgColor="F3F6F8")
        description_fill = PatternFill("solid", fgColor="DDF4F5")
        warning = PatternFill("solid", fgColor="FFF2CC")
        success = PatternFill("solid", fgColor="D9EAD3")
        exception = PatternFill("solid", fgColor="FCE4D6")
        for cell in context[1]:
            cell.fill = PatternFill("solid", fgColor="0468A3"); cell.font = Font(color="FFFFFF", bold=True, size=11)
        context.cell(2, 1).fill = description_fill
        context.cell(2, 1).font = Font(color="0468A3", bold=True)
        context.cell(2, 1).alignment = Alignment(wrap_text=True, vertical="center")
        context.row_dimensions[2].height = 36
        context.column_dimensions["A"].width = 110
        context.freeze_panes = "A2"
        category_fills = {category: green for category, _rule in rows_by_rule}
        for sheet, header_fill in ((summary, green), (general, green), (detail, navy)):
            for cell in sheet[1]:
                cell.fill = header_fill; cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            sheet.freeze_panes = "A2"; sheet.auto_filter.ref = sheet.dimensions
            for column in sheet.columns:
                letter = column[0].column_letter
                sheet.column_dimensions[letter].width = min(max(len(str(cell.value or "")) for cell in column) + 2, 42)
            for row_index in range(2, sheet.max_row + 1):
                if row_index % 2 == 0:
                    for cell in sheet[row_index]:
                        cell.fill = soft_blue
        used_sheet_names = set(book.sheetnames)
        rule_sheet_names = {}
        for category, rule in sorted(rows_by_rule):
            safe_rule = re.sub(r"[\\\\/*?:\[\]]", "_", rule)
            sheet_name = f"{safe_rule}"[:31]
            suffix = 2
            while sheet_name in used_sheet_names:
                sheet_name = f"{safe_rule[:28]}_{suffix}"
                suffix += 1
            used_sheet_names.add(sheet_name)
            rule_sheet_names[(category, rule)] = sheet_name
            detail.append([category, rule, len(rows_by_rule[(category, rule)]), sheet_name])
            detail.cell(detail.max_row, 4).hyperlink = f"#{sheet_name}!A1"
            rule_sheet = book.create_sheet(sheet_name)
            fields = sorted({
                key for _predio, row in rows_by_rule[(category, rule)] for key in row
            })
            condition_fields = [key for key in fields if str(key).lower().startswith("cond_")]
            fields = [key for key in fields if key not in condition_fields] + condition_fields
            rule_headers = [
                "Predio", *fields, "clave_caso", *EXCEPTION_HEADERS,
            ]
            last_column = len(rule_headers)
            rule_sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_column)
            rule_sheet.cell(1, 1, f"Regla incumplida: {rule}")
            rule_sheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_column)
            rule_sheet.cell(2, 1, rule_descriptions[(category, rule)] or "Descripción de la regla no disponible en el repositorio de sentencias.")
            rule_sheet.row_dimensions[2].height = 54
            rule_sheet.merge_cells(start_row=3, start_column=1, end_row=3, end_column=last_column)
            rule_sheet.cell(3, 1, self.validation_context)
            rule_sheet.row_dimensions[3].height = 30
            for column, header in enumerate(rule_headers, start=1):
                rule_sheet.cell(4, column, header)
            for index, (predio, row) in enumerate(rows_by_rule[(category, rule)], start=5):
                for column, value in enumerate([
                    predio or "Sin identificador", *[row.get(key, "") for key in fields],
                    review_by_row[id(row)].key if id(row) in review_by_row else "",
                    *(review_by_row[id(row)].exception_tracking() if id(row) in review_by_row else EXCEPTION_DEFAULTS),
                ], start=1):
                    cell = rule_sheet.cell(index, column, display(value))
                    cell.data_type = 's'
                    cell.number_format = '@'
            for cell in rule_sheet[1]:
                cell.fill = PatternFill("solid", fgColor="0468A3"); cell.font = Font(color="FFFFFF", bold=True, size=11)
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            rule_sheet.cell(2, 1).fill = description_fill
            rule_sheet.cell(2, 1).font = Font(color="0468A3", bold=True)
            rule_sheet.cell(2, 1).alignment = Alignment(wrap_text=True, vertical="center")
            rule_sheet.cell(3, 1).fill = PatternFill("solid", fgColor="EAF3F8")
            rule_sheet.cell(3, 1).font = Font(color="0468A3", italic=True)
            rule_sheet.cell(3, 1).alignment = Alignment(wrap_text=True, vertical="center")
            for cell in rule_sheet[4]:
                cell.fill = category_fills[category]; cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            rule_sheet.freeze_panes = "A5"; rule_sheet.auto_filter.ref = f"A4:{rule_sheet.cell(4, last_column).coordinate[:-1]}{rule_sheet.max_row}"
            for column_index, column in enumerate(rule_sheet.iter_cols(), start=1):
                rule_sheet.column_dimensions[get_column_letter(column_index)].width = min(max(len(str(cell.value or "")) for cell in column) + 2, 42)
            for row_index in range(5, rule_sheet.max_row + 1):
                if row_index % 2 == 0:
                    for cell in rule_sheet[row_index]:
                        cell.fill = soft_gray
            add_controls(rule_sheet, 5, rule_sheet.max_row, rule_sheet.max_column - 3)
            advance_report(f"Generando detalle de {rule}…")
        by_predio = book.create_sheet("Hallazgos por predio")
        by_predio.append(["Número predial", "Componentes", "Reglas incumplidas", "Total hallazgos", "Observación"])
        grouped_predios = defaultdict(lambda: {"components": set(), "rules": set(), "total": 0})
        for predio, component, rule, _row in error_rows:
            group = grouped_predios[predio or "Sin identificador"]
            group["components"].add(component)
            group["rules"].add(f"{component}: {rule}")
            group["total"] += 1
        for predio, values in sorted(grouped_predios.items()):
            by_predio.append([
                predio, ", ".join(sorted(values["components"])), "; ".join(sorted(values["rules"])), values["total"], "",
            ])
        for cell in by_predio[1]:
            cell.fill = navy; cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        by_predio.freeze_panes = "A2"; by_predio.auto_filter.ref = by_predio.dimensions
        for column in by_predio.columns:
            by_predio.column_dimensions[column[0].column_letter].width = min(max(len(str(cell.value or "")) for cell in column) + 2, 45)
        for row_index in range(2, by_predio.max_row + 1):
            if row_index % 2 == 0:
                for cell in by_predio[row_index]:
                    cell.fill = soft_blue
        advance_report("Generando resumen por predio…")
        technical = book.create_sheet("Errores técnicos")
        technical.append(["Componente", "Regla", "Detalle técnico"])
        technical_errors = [result for result in self.results if result.status == "Error"]
        if technical_errors:
            for result in technical_errors:
                technical.append([result.category, result.rule, result.detail])
        else:
            technical.append(["Sin errores técnicos", "", "La ejecución terminó sin errores de conexión o SQL."])
        for cell in technical[1]:
            cell.fill = red; cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        technical.freeze_panes = "A2"; technical.auto_filter.ref = technical.dimensions
        technical.column_dimensions["A"].width = 24
        technical.column_dimensions["B"].width = 18
        technical.column_dimensions["C"].width = 90
        for category in sorted({category for category, _rule in rows_by_rule}):
            package = Workbook()
            package_context = package.create_sheet("Contexto de validación", 0)
            package_context.append(["Ubicación territorial validada"])
            package_context.append([self.validation_context])
            for cell in package_context[1]:
                cell.fill = PatternFill("solid", fgColor="0468A3"); cell.font = Font(color="FFFFFF", bold=True, size=11)
            package_context.cell(2, 1).fill = description_fill
            package_context.cell(2, 1).font = Font(color="0468A3", bold=True)
            package_context.cell(2, 1).alignment = Alignment(wrap_text=True, vertical="center")
            package_context.row_dimensions[2].height = 36
            package_context.column_dimensions["A"].width = 110
            package_context.freeze_panes = "A2"
            package_index = package.active
            package_index.title = "Detalle de errores"
            package_index.append(["Componente", "Regla incumplida", "Hallazgos", "Hoja de detalle"])
            for cell in package_index[1]:
                cell.fill = green; cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            for rule in sorted(rule for item_category, rule in rows_by_rule if item_category == category):
                source = book[rule_sheet_names[(category, rule)]]
                target = package.create_sheet(source.title)
                package_index.append([category, rule, len(rows_by_rule[(category, rule)]), source.title])
                package_index.cell(package_index.max_row, 4).hyperlink = f"#{source.title}!A1"
                for source_row in source.iter_rows():
                    for cell in source_row:
                        target.cell(cell.row, cell.column, cell.value)
                for merged_range in source.merged_cells.ranges:
                    target.merge_cells(str(merged_range))
                for cell in target[1]:
                    cell.fill = PatternFill("solid", fgColor="0468A3"); cell.font = Font(color="FFFFFF", bold=True, size=11)
                    cell.alignment = Alignment(wrap_text=True, vertical="center")
                target.cell(2, 1).fill = description_fill
                target.cell(2, 1).font = Font(color="0468A3", bold=True)
                target.cell(2, 1).alignment = Alignment(wrap_text=True, vertical="center")
                target.row_dimensions[2].height = 54
                target.cell(3, 1).fill = PatternFill("solid", fgColor="EAF3F8")
                target.cell(3, 1).font = Font(color="0468A3", italic=True)
                target.cell(3, 1).alignment = Alignment(wrap_text=True, vertical="center")
                target.row_dimensions[3].height = 30
                for cell in target[4]:
                    cell.fill = green; cell.font = Font(color="FFFFFF", bold=True)
                    cell.alignment = Alignment(wrap_text=True, vertical="center")
                for row_index in range(5, target.max_row + 1):
                    if row_index % 2 == 0:
                        for cell in target[row_index]:
                            cell.fill = soft_gray
                for column_index, column in enumerate(target.iter_cols(), start=1):
                    target.column_dimensions[get_column_letter(column_index)].width = min(max(len(str(cell.value or "")) for cell in column) + 2, 42)
                target.freeze_panes = "A5"; target.auto_filter.ref = f"A4:{target.cell(4, target.max_column).coordinate[:-1]}{target.max_row}"
            package_index.freeze_panes = "A2"; package_index.auto_filter.ref = package_index.dimensions
            for column in package_index.columns:
                package_index.column_dimensions[column[0].column_letter].width = min(max(len(str(cell.value or "")) for cell in column) + 2, 36)
            safe_category = re.sub(r"[^A-Za-z0-9_-]+", "_", category).strip("_") or "paquete"
            save_review(None, [case for case in self.review_cases if case.component == category],
                        [result for result in self.results if result.category == category], workbook=package)
            link_rule_reviews(package)
            package.save(str(Path(directory) / f"detalle_{safe_category}_{stamp}.xlsx"))
            advance_report(f"Guardando paquete {category}…")
        for sheet in [detail, *[book[name] for name in rule_sheet_names.values()]]:
            book.remove(sheet)
        advance_report("Guardando reporte Excel…")
        save_review(None, self.review_cases, self.results, workbook=book)
        book.save(path)
        self.progress.setValue(report_total)
        self.export_button.setEnabled(True)
        self.status.setText("Reporte exportado correctamente.")

    @staticmethod
    def predio_from_row(row):
        preferred = ("numero_predial", "numero_predial_nacional", "npn", "codigo")
        normalized = {re.sub(r"[^a-z0-9]", "", key.lower()): value for key, value in row.items()}
        for field in preferred:
            value = normalized.get(re.sub(r"[^a-z0-9]", "", field))
            if value not in (None, ""):
                return str(value)
        return ""
