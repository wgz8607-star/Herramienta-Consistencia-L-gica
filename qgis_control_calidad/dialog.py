from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from qgis.PyQt.QtCore import QObject, QSize, QThread, QTimer, Qt, QVariant, pyqtSignal
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QDialog, QDockWidget, QDoubleSpinBox, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QProgressBar, QScrollArea, QSizePolicy, QSplitter,
    QHeaderView, QMenu, QSpinBox, QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem, QTextBrowser, QToolButton, QVBoxLayout, QWidget,
)
from qgis.core import (
    QgsApplication, QgsAuthMethodConfig, QgsDataSourceUri, QgsFeature, QgsField, QgsGeometry,
    QgsLayerTreeGroup, QgsProject, QgsSettings, QgsVectorFileWriter, QgsVectorLayer, QgsWkbTypes,
)
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from .ingestion import CicaIngestionDialog
from .reference import ReferenceDialog
from .validation_sql import COMPLEMENTARY_LAYER_INFO, LAYER_INFO, build_steps

try:
    import psycopg2
except ImportError:
    psycopg2 = None


PLUGIN_DIR = Path(__file__).resolve().parent
SQL_ROOT = PLUGIN_DIR / "resources" / "sql"
DIVIPOLA_FILE = PLUGIN_DIR / "resources" / "data" / "divipola.xlsx"
MODELS = {"Modelo Interno de Levantamiento 1.0": "rules_int_model", "CICA": "rules_cica_db"}
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
    "user": "consulta_sentencias",
    "password": "",
}
ALLOWED_POSTGRES_HOST = "172.19.3.225"

GRAPHICAL_GROUPS = (
    ("0. Errores de geometría", 0, 0),
    ("1. No debe haber huecos", 1, 16),
    ("2. No debe superponerse", 17, 37),
    ("3. Debe estar totalmente contenido (cubierto) por", 38, 53),
    ("4. Deben cubrirse entre sí", 54, 57),
    ("5. Deben coincidir sus atributos", 58, 71),
    ("6. Validaciones complementarias", 72, 83),
)

ERROR_GROUP_STYLES = {
    "0. Errores de geometría": (QColor(235, 45, 45, 105), QColor(150, 0, 0)),
    "1. No debe haber huecos": (QColor(255, 214, 10, 115), QColor(170, 112, 0)),
    "2. No debe superponerse": (QColor(224, 35, 145, 105), QColor(145, 0, 84)),
    "3. Debe estar totalmente contenido (cubierto) por": (QColor(255, 126, 24, 110), QColor(175, 65, 0)),
    "4. Deben cubrirse entre sí": (QColor(25, 112, 230, 100), QColor(0, 55, 150)),
    "5. Deben coincidir sus atributos": (QColor(137, 61, 190, 105), QColor(78, 24, 125)),
    "6. Validaciones complementarias": (QColor(0, 170, 150, 105), QColor(0, 92, 82)),
}

CONTAINMENT_LAYER_NAMES = {
    "1": "CR_Terreno (Predios formales)",
    "2": "CR_Terreno (Predios informales)",
    "17": "CR_Terreno (Predios formales)",
    "18": "CR_Terreno (Predios informales)",
    "19": "CC_Manzana",
    "20": "CR_Terreno (Posesión informal) - CR_Terreno público",
    "21": "CR_Terreno (Ocupación informal) - CR_Terreno privado",
    "38": "CC_CentroPoblado - CC_LimiteMunicipio o CC_Corregimiento",
    "39": "CC_PerimetroUrbano - CC_LimiteMunicipio o CC_Corregimiento",
    "40": "CC_SectorUrbano - CC_CentroPoblado o CC_PerimetroUrbano",
    "41": "CC_SectorRural - CC_LimiteMunicipio o CC_Corregimiento",
    "42": "CC_Vereda - CC_SectorRural",
    "43": "CC_LocalidadComuna - CC_SectorUrbano",
    "44": "CC_Barrio - CC_LocalidadComuna",
    "45": "CC_Manzana - CC_Barrio",
    "46": "ExtDireccion - CR_Terreno",
    "47": "CR_UnidadConstruccion (Formal) - CR_Terreno (Formal)",
    "48": "CR_UnidadConstruccion (Informal) - CR_Terreno (Informal)",
    "49": "CR_Terreno (Urbano) - VM_ZonaHomogeneaGeoeconomicaUrbana",
    "50": "CR_Terreno (Urbano) - VM_ZonaHomogeneaFisicaUrbana",
    "51": "CR_Terreno (Rural) - VM_ZonaHomogeneaGeoeconomicaRural",
    "52": "CR_Terreno (Rural) - VM_ZonaHomogeneaFisicaRural",
    "53": "CR_Terreno (Informal) - CR_Terreno (Formal)",
    "54": "CR_Terreno (Urbano) - CC_Manzana",
    "55": "CR_Terreno (Rural) - CC_Vereda",
    "56": "VM_ZonaHomogeneaGeoeconomicaRural - VM_ZonaHomogeneaFisicaRural",
    "57": "VM_ZonaHomogeneaGeoeconomicaUrbana - VM_ZonaHomogeneaFisicaUrbana",
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
                            cursor.execute(
                                f"SELECT version, max(descripcion_regla), 'PUBLICADA', max(fecha_actualizacion) "
                                f"FROM public.{table} WHERE activa GROUP BY version ORDER BY max(fecha_actualizacion) DESC, version DESC"
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


class SpatialStatisticsDialog(QDialog):
    """Presenta el inventario y conteo de las capas espaciales del esquema."""

    def __init__(self, parent, schema, rows):
        super().__init__(parent)
        self.setWindowTitle(f"Estadística de elementos espaciales · {schema}")
        self.resize(900, 520)
        layout = QVBoxLayout(self)
        title = QLabel(f"Capas espaciales presentes en el esquema: {schema}")
        title.setStyleSheet("font-size: 17px; font-weight: 700; color: #0468A3;")
        layout.addWidget(title)
        detail = QLabel("Conteos informativos obtenidos directamente de PostgreSQL/PostGIS. La fuente no se modifica.")
        detail.setWordWrap(True)
        layout.addWidget(detail)

        valuation_prefixes = ("av_", "vm_")
        cartographic_prefixes = ("cc_",)
        valuation_rows = [row for row in rows if row["table"].lower().startswith(valuation_prefixes)]
        cartographic_rows = [row for row in rows if row["table"].lower().startswith(cartographic_prefixes)]
        terrain_rows = [
            row for row in rows
            if not row["table"].lower().startswith(cartographic_prefixes + valuation_prefixes)
        ]

        def statistics_page(group_rows):
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(7, 9, 7, 7)
            table = QTableWidget(len(group_rows) + 1, 7)
            table.setHorizontalHeaderLabels([
                "Capa", "Columna geométrica", "Tipo", "SRID",
                "Registros", "Con geometría", "Nulas / vacías",
            ])
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setAlternatingRowColors(True)
            totals = [0, 0, 0]
            for row_index, row in enumerate(group_rows):
                values = (
                    row["table"], row["geometry_column"], row["type"], row["srid"],
                    row["total"], row["with_geometry"], f'{row["null"]} / {row["empty"]}',
                )
                totals[0] += row["total"]
                totals[1] += row["with_geometry"]
                totals[2] += row["null"] + row["empty"]
                for column, value in enumerate(values):
                    table.setItem(row_index, column, QTableWidgetItem(str(value)))
            total_row = len(group_rows)
            total_values = ("TOTAL DEL GRUPO", "", "", "", totals[0], totals[1], totals[2])
            for column, value in enumerate(total_values):
                item = QTableWidgetItem(str(value))
                table.setItem(total_row, column, item)
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setBackground(QColor("#DDF4F5"))
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setStyleSheet(
                "QTableWidget { background: white; gridline-color: #D7EAF7; border: 1px solid #3FA4F5; } "
                "QHeaderView::section { background: #068CBB; color: white; padding: 6px; font-weight: 700; }"
            )
            page_layout.addWidget(table, 1)
            group_summary = QLabel(
                f"{len(group_rows)} capas · {totals[0]} registros · {totals[1]} geometrías presentes · "
                f"{totals[2]} nulas o vacías"
            )
            group_summary.setStyleSheet("font-weight: 700; color: #575756;")
            page_layout.addWidget(group_summary)
            return page

        groups = QTabWidget()
        groups.addTab(statistics_page(terrain_rows), f"Información predial ({len(terrain_rows)})")
        groups.addTab(statistics_page(cartographic_rows), f"Cartografía catastral ({len(cartographic_rows)})")
        groups.addTab(statistics_page(valuation_rows), f"Avalúos ({len(valuation_rows)})")
        layout.addWidget(groups, 1)
        total_records = sum(row["total"] for row in rows)
        total_geometries = sum(row["with_geometry"] for row in rows)
        summary = QLabel(f"Total general: {len(rows)} capas espaciales · {total_records} registros · {total_geometries} geometrías presentes")
        summary.setStyleSheet("font-weight: 700; color: #575756;")
        layout.addWidget(summary)
        buttons = QHBoxLayout()
        buttons.addStretch()
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)


class HelpDialog(QDialog):
    """Ayuda funcional y catálogo de controles del componente gráfico."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayuda · Validador Consistencia Lógica Alfanumérica")
        self.resize(920, 620)
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        recommendations = QTextBrowser()
        recommendations.setHtml("""
        <h2>Recomendaciones de uso</h2>
        <ul>
          <li><b>Servidor autorizado:</b> el complemento solamente permite conexiones PostgreSQL al anfitrión <code>172.19.3.225</code>.</li>
          <li>Puede utilizarse un usuario de consulta. Requiere <code>CONNECT</code> y <code>TEMP</code> sobre la base, <code>USAGE</code> sobre el esquema y <code>SELECT</code> sobre las tablas involucradas.</li>
          <li>No se requieren permisos de edición, creación de esquemas ni modificación de las capas fuente.</li>
          <li>Verifique el sistema de referencia y las clases presentes antes de ejecutar.</li>
          <li>Revise la tolerancia geométrica y el área mínima de acuerdo con el proyecto.</li>
          <li>Los resultados se crean únicamente como capas temporales en QGIS.</li>
          <li>La base y el esquema fuente nunca se modifican.</li>
          <li>Las capas temporales desaparecen al cerrar QGIS; expórtelas al GeoPackage para conservarlas.</li>
          <li>Las geometrías nulas se presentan como tablas, pues no tienen ubicación en el mapa.</li>
          <li>Un hallazgo puede requerir revisión técnica antes de clasificarse como error definitivo.</li>
          <li>Al repetir la validación se reemplazan los grupos de resultados cargados por la herramienta.</li>
        </ul>
        """)
        validations = QTextBrowser()
        geometry_items = [
            ("0.1", "Geometrías inválidas"), ("0.2", "Policurvas"),
            ("0.3", "Geometrías nulas"), ("0.4", "Geometrías vacías"),
            ("0.5", "Tipo geométrico incorrecto"), ("0.6", "Sistema de referencia incorrecto"),
            ("0.7", "Geometrías duplicadas (excepto CR_Terreno y CR_UnidadConstruccion)"),
            ("0.8", "Partes repetidas dentro de una geometría"),
        ]
        sections = defaultdict(list)
        for code, name in geometry_items:
            sections["0. Errores de geometría"].append((code, name))
        for _layer, code, description in LAYER_INFO:
            number = int(code)
            category = next(name for name, start, end in GRAPHICAL_GROUPS if start <= number <= end)
            sections[category].append((code, description))
        sections["6. Validaciones complementarias"].extend(
            (code, description) for _layer, code, description in COMPLEMENTARY_LAYER_INFO
        )
        html = ["<h2>Validaciones realizadas</h2>"]
        for section, items in sections.items():
            html.append(f"<h3>{section}</h3><ul>")
            html.extend(f"<li><b>{code}</b> · {description}</li>" for code, description in items)
            html.append("</ul>")
        validations.setHtml("".join(html))
        tabs.addTab(recommendations, "Recomendaciones")
        tabs.addTab(validations, "Validaciones realizadas")
        layout.addWidget(tabs, 1)
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(close_button)
        layout.addLayout(buttons)


class RuleWorker(QObject):
    result = pyqtSignal(object)
    general_report = pyqtSignal(object, str)
    progress = pyqtSignal(int, int)
    fatal_error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, params, schema, prefix, r1_table, rules, general_report_path=None,
                 minimum_area=0.001, maximum_e_area=1, geometry_tolerance=0):
        super().__init__()
        self.params = params
        self.schema = schema
        self.prefix = prefix
        self.r1_table = r1_table
        self.rules = rules
        self.general_report_path = general_report_path
        self.minimum_area = float(minimum_area)
        self.maximum_e_area = float(maximum_e_area)
        self.geometry_tolerance = float(geometry_tolerance)

    def resolve_sql(self, sql):
        schema_prefix = self.schema.rstrip(".") + "."
        sql = sql.replace("{esquema}.{punto}", schema_prefix)
        sql = sql.replace("{esquema}{punto}.", schema_prefix)
        sql = sql.replace("{esquema}{punto}", schema_prefix)
        sql = sql.replace("{esquema}", schema_prefix).replace("{punto}", self.prefix)
        for marker, value in (
            ("{area_minima}", self.minimum_area),
            ("{area_maxima_e}", self.maximum_e_area),
            ("{tolerancia_geometrica}", self.geometry_tolerance),
        ):
            sql = sql.replace(marker, str(value))
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
                        detail_rows = [dict(zip(fields, row)) for row in rows]
                        self.result.emit(RuleResult(rule_name, category, "Correcta", len(rows), rows=detail_rows, description=description))
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


class GraphicalRuleWorker(QObject):
    result = pyqtSignal(object)
    progress = pyqtSignal(int, int)
    activity = pyqtSignal(str, int, int)
    cancelled = pyqtSignal()
    fatal_error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, params, source_schema, output_schema, selected_layers, area_maximum,
                 area_minimum, tolerance, replace_output, temporary_output, validate_geometry=False,
                 minimum_width=0.001, exclude_micro_errors=True):
        super().__init__()
        self.params = params
        self.source_schema = source_schema
        self.output_schema = output_schema
        self.selected_layers = selected_layers
        self.area_maximum = area_maximum
        self.area_minimum = area_minimum
        self.tolerance = tolerance
        self.replace_output = replace_output
        self.temporary_output = temporary_output
        self.validate_geometry = validate_geometry
        self.minimum_width = max(0.0, float(minimum_width))
        self.exclude_micro_errors = exclude_micro_errors
        self._cancel_requested = False
        self._connection = None

    def request_cancel(self):
        """Solicita cancelación y, si hay una consulta activa, pide a PostgreSQL interrumpirla."""
        self._cancel_requested = True
        connection = self._connection
        if connection is not None:
            try:
                connection.cancel()
            except Exception:
                pass

    @staticmethod
    def category_for_code(code):
        if str(code).upper() in {item[1] for item in COMPLEMENTARY_LAYER_INFO}:
            return "6. Validaciones complementarias"
        number = int(code)
        return next(name for name, start, end in GRAPHICAL_GROUPS if start <= number <= end)

    def run(self):
        try:
            steps = build_steps(
                self.source_schema, self.output_schema, self.area_maximum,
                self.area_minimum, self.tolerance,
                [item[0] for item in self.selected_layers],
                self.minimum_width,
            ) if self.selected_layers else []
            geometry_progress = 8 if self.validate_geometry else 0
            total = max(len(steps) + len(self.selected_layers) + geometry_progress, 1)
            with psycopg2.connect(**self.params) as connection:
                self._connection = connection
                with connection.cursor() as cursor:
                    session_temporary = self.output_schema == "pg_temp"
                    if session_temporary:
                        cursor.execute(
                            "SELECT has_database_privilege(current_user, current_database(), 'TEMP')"
                        )
                        if not cursor.fetchone()[0]:
                            raise ValueError(
                                "El usuario de consulta necesita el privilegio TEMP en esta base de datos "
                                "para ejecutar la validación sin crear esquemas ni modificar la fuente."
                            )
                    if not session_temporary:
                        cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = %s)", (self.output_schema,))
                        exists = cursor.fetchone()[0]
                        if exists and not (self.replace_output or self.temporary_output):
                            raise ValueError(
                                f"El esquema de resultados {self.output_schema} ya existe. Active la opción para reemplazarlo."
                            )
                        if exists:
                            quoted = '"' + self.output_schema.replace('"', '""') + '"'
                            cursor.execute(f"DROP SCHEMA {quoted} CASCADE")
                    if not steps and not session_temporary:
                        quoted = '"' + self.output_schema.replace('"', '""') + '"'
                        cursor.execute(f"CREATE SCHEMA {quoted}")
                    for index, (_label, statement) in enumerate(steps, 1):
                        if self._cancel_requested:
                            connection.rollback()
                            self.cancelled.emit()
                            return
                        self.activity.emit(str(_label), index - 1, total)
                        cursor.execute(statement)
                        self.progress.emit(index, total)
                    progress_index = len(steps)
                    if self.validate_geometry:
                        quoted_source = '"' + self.source_schema.replace('"', '""') + '"'
                        quoted_output = '"' + self.output_schema.replace('"', '""') + '"'
                        cursor.execute(
                            "SELECT f_table_name, f_geometry_column, type FROM geometry_columns "
                            "WHERE f_table_schema = %s ORDER BY f_table_name, f_geometry_column",
                            (self.source_schema,),
                        )
                        source_geometries = cursor.fetchall()
                        cursor.execute(
                            "SELECT srid FROM geometry_columns WHERE f_table_schema=%s AND srid>0 "
                            "GROUP BY srid ORDER BY count(*) DESC, srid LIMIT 1",
                            (self.source_schema,),
                        )
                        srid_row = cursor.fetchone()
                        expected_srid = int(srid_row[0]) if srid_row else 0
                        geometry_labels = {
                            "0.1": "Geometrías inválidas",
                            "0.2": "Policurvas",
                            "0.3": "Geometrías nulas",
                            "0.4": "Geometrías vacías",
                            "0.5": "Tipo geométrico incorrecto",
                            "0.6": "Sistema de referencia incorrecto",
                            "0.7": "Geometrías duplicadas",
                            "0.8": "Partes repetidas dentro de una geometría",
                        }
                        geometry_checks = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 8), (7, 10), (8, 11))
                        for check_number, query_number in geometry_checks:
                            if self._cancel_requested:
                                connection.rollback()
                                self.cancelled.emit()
                                return
                            code = f"0.{check_number}"
                            label = geometry_labels[code]
                            self.activity.emit(f"{code} · {label}", progress_index, total)
                            check_emitted = False
                            for table, geometry_column, declared_type in source_geometries:
                                if self._cancel_requested:
                                    connection.rollback()
                                    self.cancelled.emit()
                                    return
                                quoted_table = '"' + table.replace('"', '""') + '"'
                                quoted_geometry = '"' + geometry_column.replace('"', '""') + '"'
                                geom = f"t.{quoted_geometry}"
                                normalized_table = re.sub(r"[^a-z0-9]", "", table.lower())
                                if query_number == 1:
                                    select_sql = (
                                        f"SELECT (row_number() OVER ())::text registro_origen, ST_IsValidReason({geom}) motivo, {geom} geometria "
                                        f"FROM {quoted_source}.{quoted_table} t WHERE {geom} IS NOT NULL AND NOT ST_IsValid({geom})"
                                    )
                                elif query_number == 2:
                                    select_sql = (
                                        f"SELECT (row_number() OVER ())::text registro_origen, 'Contiene arcos o curvas'::text motivo, {geom} geometria "
                                        f"FROM {quoted_source}.{quoted_table} t WHERE {geom} IS NOT NULL AND ST_HasArc({geom})"
                                    )
                                elif query_number == 3:
                                    select_sql = (
                                        f"SELECT (row_number() OVER ())::text registro_origen, 'Geometría NULL'::text motivo "
                                        f"FROM {quoted_source}.{quoted_table} t WHERE {geom} IS NULL"
                                    )
                                elif query_number == 4:
                                    select_sql = (
                                        f"SELECT (row_number() OVER ())::text registro_origen, 'Geometría vacía'::text motivo, {geom} geometria "
                                        f"FROM {quoted_source}.{quoted_table} t WHERE {geom} IS NOT NULL AND ST_IsEmpty({geom})"
                                    )
                                elif query_number == 5:
                                    if "direccion" in normalized_table:
                                        allowed_types = "'POINT','MULTIPOINT'"
                                        expected_type = "punto"
                                    elif any(marker in normalized_table for marker in (
                                        "terreno", "construccion", "manzana", "vereda", "sector", "barrio",
                                        "localidad", "corregimiento", "centropoblado", "perimetro", "limite",
                                        "zonahomogenea",
                                    )):
                                        allowed_types = "'POLYGON','MULTIPOLYGON'"
                                        expected_type = "polígono"
                                    else:
                                        base_type = str(declared_type).upper().replace("MULTI", "")
                                        if base_type not in ("POINT", "LINESTRING", "POLYGON"):
                                            continue
                                        multi_type = "MULTI" + base_type
                                        allowed_types = f"'{base_type}','{multi_type}'"
                                        expected_type = base_type.lower()
                                    select_sql = (
                                        f"SELECT (row_number() OVER ())::text registro_origen, "
                                        f"('Se esperaba {expected_type}; se encontró ' || GeometryType({geom}))::text motivo, {geom} geometria "
                                        f"FROM {quoted_source}.{quoted_table} t WHERE {geom} IS NOT NULL "
                                        f"AND upper(GeometryType({geom})) NOT IN ({allowed_types})"
                                    )
                                elif query_number == 8:
                                    if not expected_srid:
                                        continue
                                    select_sql = (
                                        f"SELECT (row_number() OVER ())::text registro_origen, "
                                        f"('SRID ' || ST_SRID({geom}) || '; se esperaba {expected_srid}')::text motivo, {geom} geometria "
                                        f"FROM {quoted_source}.{quoted_table} t WHERE {geom} IS NOT NULL "
                                        f"AND ST_SRID({geom}) <> {expected_srid}"
                                    )
                                elif query_number == 10:
                                    if normalized_table in ("crterreno", "crunidadconstruccion"):
                                        continue
                                    select_sql = (
                                        f"WITH datos AS (SELECT row_number() OVER () AS rid, {quoted_geometry} AS geometria "
                                        f"FROM {quoted_source}.{quoted_table} WHERE {quoted_geometry} IS NOT NULL) "
                                        f"SELECT a.rid::text registro_origen, b.rid::text registro_duplicado, "
                                        f"'Geometría exactamente duplicada'::text motivo, a.geometria "
                                        f"FROM datos a JOIN datos b ON a.rid < b.rid "
                                        f"AND a.geometria && b.geometria "
                                        f"AND ST_AsEWKB(a.geometria) = ST_AsEWKB(b.geometria)"
                                    )
                                else:
                                    select_sql = (
                                        f"SELECT (row_number() OVER ())::text registro_origen, 'Partes idénticas repetidas'::text motivo, {geom} geometria "
                                        f"FROM {quoted_source}.{quoted_table} t WHERE {geom} IS NOT NULL "
                                        f"AND ST_NumGeometries({geom}) > 1 AND EXISTS ("
                                        f"SELECT 1 FROM ST_Dump({geom}) a CROSS JOIN ST_Dump({geom}) b "
                                        f"WHERE a.path < b.path AND ST_AsEWKB(a.geom)=ST_AsEWKB(b.geom))"
                                    )
                                cursor.execute(
                                    f"SELECT EXISTS (SELECT 1 FROM ({select_sql}) validacion LIMIT 1)"
                                )
                                if not cursor.fetchone()[0]:
                                    continue
                                safe_table = re.sub(r"[^A-Za-z0-9_]", "_", table.lower())[:36]
                                output_table = f"g{check_number:02d}_{safe_table}"
                                quoted_result = '"' + output_table.replace('"', '""') + '"'
                                cursor.execute(
                                    f"CREATE TABLE {quoted_output}.{quoted_result} AS {select_sql}"
                                )
                                if query_number == 3:
                                    cursor.execute(f"SELECT * FROM {quoted_output}.{quoted_result}")
                                else:
                                    cursor.execute(
                                        f"SELECT *, ST_AsBinary(ST_CurveToLine(geometria)) AS qgis_wkb "
                                        f"FROM {quoted_output}.{quoted_result}"
                                    )
                                fields = [column.name for column in cursor.description]
                                rows = [dict(zip(fields, row)) for row in cursor.fetchall()]
                                self.result.emit(RuleResult(
                                    code, "0. Errores de geometría", "Correcta", len(rows), rows=rows,
                                    description=f"{table} - {label}",
                                ))
                                check_emitted = True
                            if not check_emitted:
                                self.result.emit(RuleResult(
                                    code, "0. Errores de geometría", "Correcta", 0, rows=[], description=label,
                                ))
                            progress_index += 1
                            self.progress.emit(progress_index, total)
                    for offset, (layer_name, code, description) in enumerate(self.selected_layers, progress_index + 1):
                        if self._cancel_requested:
                            connection.rollback()
                            self.cancelled.emit()
                            return
                        self.activity.emit(f"{code} · {description}", offset - 1, total)
                        quoted_schema = '"' + self.output_schema.replace('"', '""') + '"'
                        quoted_layer = '"' + layer_name.replace('"', '""') + '"'
                        # La exclusión de residuos de precisión debe aplicarse a
                        # todos los resultados poligonales, incluidos los controles
                        # de coincidencia de atributos (58–71). El filtro SQL de
                        # abajo ya deja intactas las geometrías puntuales y lineales.
                        filter_micro = self.exclude_micro_errors
                        if filter_micro:
                            cursor.execute(
                                f"ALTER TABLE {quoted_schema}.{quoted_layer} "
                                f"ADD COLUMN IF NOT EXISTS perimetro_m numeric, "
                                f"ADD COLUMN IF NOT EXISTS ancho_equiv_m numeric, "
                                f"ADD COLUMN IF NOT EXISTS clasificacion text"
                            )
                            cursor.execute(
                                f"UPDATE {quoted_schema}.{quoted_layer} SET "
                                f"perimetro_m=round(ST_Perimeter(geometria)::numeric,6), "
                                f"ancho_equiv_m=round((CASE WHEN ST_Perimeter(geometria)>0 "
                                f"THEN 2*ST_Area(geometria)/ST_Perimeter(geometria) ELSE 0 END)::numeric,9), "
                                f"clasificacion='Error reportable' "
                                f"WHERE geometria IS NOT NULL AND upper(GeometryType(geometria)) IN ('POLYGON','MULTIPOLYGON')"
                            )
                            cursor.execute(
                                f"DELETE FROM {quoted_schema}.{quoted_layer} WHERE geometria IS NOT NULL "
                                f"AND upper(GeometryType(geometria)) IN ('POLYGON','MULTIPOLYGON') "
                                f"AND (ST_Area(geometria)<%s OR (CASE WHEN ST_Perimeter(geometria)>0 "
                                f"THEN 2*ST_Area(geometria)/ST_Perimeter(geometria) ELSE 0 END)<%s)",
                                (self.area_minimum, self.minimum_width),
                            )
                        # psycopg2 puede devolver PostGIS geometry como texto EWKB hexadecimal.
                        # Se agrega una copia WKB OGC explícita para que QGIS la interprete de
                        # forma consistente, independientemente de la configuración del servidor.
                        cursor.execute(
                            f"SELECT *, ST_AsBinary(geometria) AS qgis_wkb "
                            f"FROM {quoted_schema}.{quoted_layer}"
                        )
                        fields = [column.name for column in cursor.description]
                        rows = [dict(zip(fields, row)) for row in cursor.fetchall()]
                        if not rows:
                            cursor.execute(f"DROP TABLE {quoted_schema}.{quoted_layer}")
                        self.result.emit(RuleResult(
                            code, self.category_for_code(code), "Correcta", len(rows),
                            rows=rows, description=description,
                        ))
                        self.progress.emit(offset, total)
                    if self.temporary_output:
                        # Todos los resultados ya fueron copiados a memoria. La
                        # transacción completa se revierte para que PostgreSQL no
                        # conserve esquemas, tablas ni vistas de procesamiento.
                        connection.rollback()
        except Exception as error:
            if self._cancel_requested:
                self.cancelled.emit()
            else:
                self.fatal_error.emit(re.sub(r"\s+", " ", str(error)).strip()[:600])
        finally:
            self._connection = None
            self.finished.emit()


class ControlCalidadDialog(QWidget):
    def __init__(self, parent=None, iface=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("Validador Consistencia Lógica Alfanumérica")
        self.setWindowIcon(QIcon(str(PLUGIN_DIR / "icon.svg")))
        self.resize(420, 520)
        self.results: list[RuleResult] = []
        self.general_report_rows = []
        self.general_report_error = ""
        self.validation_context = "Ubicación territorial pendiente de identificar."
        self.selected_sql_version = None
        self.repository_rules = []
        self.thread = None
        self.worker = None
        self.execution_failed = False
        self.execution_cancelled = False
        self.output_failed = False
        self.expected_rule_count = 0
        self.current_activity = "Pendiente de iniciar"
        self.execution_started_at = None
        self.execution_timer = QTimer(self)
        self.execution_timer.setInterval(1000)
        self.execution_timer.timeout.connect(self.update_live_progress)
        self.loaded_error_group_key = "control_calidad/error_layers"
        self.category_checks = {}
        self.references_ready = False
        self._build()
        self.refresh_categories()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(6)
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

        self.heading = QLabel("Validador Consistencia Lógica Alfanumérica")
        self.heading.setWordWrap(True)
        self.heading.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.heading.setStyleSheet("font-size: 18px; font-weight: 700; color: #0468A3;")
        heading_row = QHBoxLayout()
        heading_row.addWidget(self.heading, 1)
        self.compact_status = QLabel("Listo")
        self.compact_status.setStyleSheet("color: #52666a; font-weight: 600;")
        self.compact_status.setVisible(False)
        heading_row.addWidget(self.compact_status)
        layout.addLayout(heading_row)

        header_actions = QHBoxLayout()
        header_actions.setSpacing(5)
        self.collapse_button = QPushButton("Contraer")
        self.collapse_button.setToolTip("Contrae el panel y conserva visible el estado de la validación.")
        self.collapse_button.clicked.connect(self.toggle_compact_view)
        header_actions.addWidget(self.collapse_button)
        self.minimize_button = QPushButton("Minimizar")
        self.minimize_button.setToolTip("Oculta el panel acoplado o minimiza la ventana flotante. El proceso continúa.")
        self.minimize_button.clicked.connect(self.minimize_panel)
        header_actions.addWidget(self.minimize_button)
        help_link = QLabel('<a href="help">Ayuda</a>')
        help_link.setToolTip("Abrir recomendaciones y listado de validaciones")
        help_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        help_link.setOpenExternalLinks(False)
        help_link.linkActivated.connect(lambda _link: HelpDialog(self).exec_())
        header_actions.addWidget(help_link)
        header_actions.addStretch()
        layout.addLayout(header_actions)
        self.subtitle = QLabel("Validación de consistencia lógica alfanumérica")
        self.subtitle.setStyleSheet("color: #52666a;")
        layout.addWidget(self.subtitle)

        self.tabs = QTabWidget(self)
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #B8D7E8; background: #F5F7F8; border-radius: 5px; } "
            "QTabBar::tab { background: #DCEAF1; color: #575756; padding: 9px 18px; margin-right: 2px; "
            "border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: 600; } "
            "QTabBar::tab:selected { background: #068CBB; color: white; }"
        )
        layout.addWidget(self.tabs, 1)

        setup_page = QWidget()
        setup_page_layout = QVBoxLayout(setup_page)
        setup_page_layout.setContentsMargins(6, 6, 6, 6)
        setup_page_layout.setSpacing(5)
        self.section_tabs = QTabWidget(setup_page)
        self.section_tabs.setDocumentMode(True)
        self.section_tabs.tabBar().setExpanding(True)
        self.section_tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #00AFC2; background: #F7FAFB; border-radius: 5px; } "
            "QTabBar::tab { background: #E2F7F8; color: #0468A3; padding: 7px 7px; "
            "border: 1px solid #9DDDE2; font-weight: 700; min-width: 90px; } "
            "QTabBar::tab:selected { background: #068CBB; color: white; border-color: #068CBB; }"
        )
        setup_page_layout.addWidget(self.section_tabs, 1)
        connection = QGroupBox("1. Conexión a PostgreSQL / PostGIS")
        style_section(connection, "#575756")
        form = QFormLayout(connection)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.model = QComboBox()
        self.model.addItems(MODELS)
        self.model.currentTextChanged.connect(self.refresh_categories)
        self.model.currentTextChanged.connect(self.update_ingestion_button)
        self.model.currentTextChanged.connect(self.model_changed)
        self.connection_mode = QComboBox()
        self.connection_mode.addItems(["Conexión guardada en QGIS", "Conexión manual a PostgreSQL"])
        self.connection_mode.currentIndexChanged.connect(self.change_connection_mode)
        self.connection_stack = QStackedWidget()
        self.connection_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.qgis_connection = QComboBox()
        self.qgis_connection.currentTextChanged.connect(self.describe_qgis_connection)
        qgis_page = QWidget()
        qgis_layout = QFormLayout(qgis_page)
        qgis_layout.setContentsMargins(0, 0, 0, 0)
        qgis_layout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        qgis_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        qgis_row = QHBoxLayout()
        qgis_row.addWidget(self.qgis_connection, 1)
        refresh_qgis = QPushButton("Actualizar")
        refresh_qgis.clicked.connect(self.load_qgis_connections)
        qgis_layout.addRow("Conexión de QGIS", qgis_row)
        qgis_layout.addRow("", refresh_qgis)
        self.qgis_description = QLabel("Seleccione una conexión guardada en QGIS.")
        self.qgis_description.setWordWrap(True)
        self.qgis_description.setStyleSheet("color: #52666a;")
        qgis_layout.addRow("", self.qgis_description)
        self.connection_stack.addWidget(qgis_page)
        manual_page = QWidget()
        manual_form = QFormLayout(manual_page)
        manual_form.setContentsMargins(0, 0, 0, 0)
        manual_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        manual_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.host = QLineEdit(ALLOWED_POSTGRES_HOST)
        self.host.setReadOnly(True)
        self.host.setToolTip("Servidor PostgreSQL autorizado para este complemento")
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
        self.schema.currentTextChanged.connect(self.update_territorial_identification)
        self.sql_version_label = QLabel("Seleccione una versión de SQL")
        choose_sql_version = QPushButton("Buscar versión de sentencias…")
        choose_sql_version.clicked.connect(self.open_sql_version_dialog)
        version_row = QHBoxLayout()
        version_row.addWidget(self.sql_version_label, 1)
        version_row.addWidget(choose_sql_version)
        self.ingestion_label = QLabel("Ingesta CICA")
        self.ingestion_button = QPushButton("Cargar insumos CICA…")
        self.ingestion_button.clicked.connect(self.open_ingestion)
        self.published_r1 = QComboBox()
        self.published_r2 = QComboBox()
        self.refresh_references = QPushButton("Actualizar referencias publicadas")
        self.refresh_references.clicked.connect(self.load_public_references)
        self.published_r1.setEnabled(False)
        self.published_r2.setEnabled(False)
        self.refresh_references.setEnabled(False)
        form.addRow("Forma de conexión", self.connection_mode)
        form.addRow("", self.connection_stack)
        test = QPushButton("Listar esquemas")
        test.clicked.connect(self.test_connection)
        form.addRow("", test)
        form.addRow("Esquema a validar", self.schema)
        self.territory_label = QLabel("Departamento y municipio: liste los esquemas y seleccione uno.")
        self.territory_label.setWordWrap(True)
        self.territory_label.setStyleSheet(
            "color: #0468A3; font-weight: 700; background: #E2F7F8; border-radius: 4px; padding: 6px;"
        )
        form.addRow("Ubicación", self.territory_label)
        connection.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.section_tabs.addTab(
            self._make_section_page(
                connection,
                "La contraseña no se guarda. Las consultas no modifican la fuente.",
            ),
            "1. Conexión",
        )
        self.section_tabs.setTabToolTip(0, "Conexión a PostgreSQL / PostGIS")

        parameters = QGroupBox("2. Parámetros de validación y salida")
        style_section(parameters, "#00C7CB")
        parameter_form = QFormLayout(parameters)
        parameter_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        parameter_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        virtual_output = QLabel("Capas virtuales/temporales en QGIS")
        virtual_output.setStyleSheet("color: #0468A3; font-weight: 700;")
        self.minimum_area = QDoubleSpinBox()
        self.minimum_area.setRange(0, 1000)
        self.minimum_area.setDecimals(6)
        self.minimum_area.setSingleStep(0.001)
        self.minimum_area.setValue(0.001)
        self.minimum_area.setSuffix(" m²")
        self.minimum_width = QDoubleSpinBox()
        self.minimum_width.setRange(0, 10)
        self.minimum_width.setDecimals(6)
        self.minimum_width.setSingleStep(0.001)
        self.minimum_width.setValue(0.001)
        self.minimum_width.setSuffix(" m")
        self.exclude_micro_errors = QCheckBox("Excluir microerrores de precisión")
        self.exclude_micro_errors.setChecked(True)
        self.maximum_e_area = QSpinBox()
        self.maximum_e_area.setRange(1, 1000000)
        self.maximum_e_area.setValue(1)
        self.maximum_e_area.setSuffix(" m²")
        self.geometry_tolerance = QDoubleSpinBox()
        self.geometry_tolerance.setRange(0, 10)
        self.geometry_tolerance.setDecimals(4)
        self.geometry_tolerance.setSingleStep(0.001)
        self.geometry_tolerance.setValue(0)
        self.geometry_tolerance.setSuffix(" m")
        self.auto_load_layers = QCheckBox("Cargar capas de error al terminar")
        self.auto_load_layers.setChecked(True)
        self.auto_export_gpkg = QCheckBox("Exportar resultados a un GeoPackage")
        self.gpkg_path = QLineEdit()
        self.gpkg_path.setPlaceholderText("Seleccione el archivo .gpkg")
        self.gpkg_button = QPushButton("Examinar…")
        self.gpkg_button.clicked.connect(self.choose_gpkg_path)
        gpkg_row = QHBoxLayout()
        gpkg_row.addWidget(self.gpkg_path, 1)
        gpkg_row.addWidget(self.gpkg_button)
        self.replace_gpkg = QCheckBox("Reemplazar el GeoPackage si ya existe")
        self.auto_export_excel = QCheckBox("Generar resumen Excel")
        self.excel_path = QLineEdit()
        self.excel_path.setPlaceholderText("Seleccione el archivo .xlsx")
        self.excel_button = QPushButton("Examinar…")
        self.excel_button.clicked.connect(self.choose_excel_path)
        excel_row = QHBoxLayout()
        excel_row.addWidget(self.excel_path, 1)
        excel_row.addWidget(self.excel_button)
        self.replace_excel = QCheckBox("Reemplazar el Excel si ya existe")
        parameter_form.addRow("Resultados", virtual_output)
        parameter_form.addRow("Área mínima reportable", self.minimum_area)
        parameter_form.addRow("Ancho mínimo reportable", self.minimum_width)
        parameter_form.addRow("", self.exclude_micro_errors)
        parameter_form.addRow("Área máxima para controles E", self.maximum_e_area)
        parameter_form.addRow("Tolerancia geométrica", self.geometry_tolerance)
        parameter_form.addRow("", self.auto_load_layers)
        parameter_form.addRow("", self.auto_export_gpkg)
        parameter_form.addRow("Archivo GeoPackage", gpkg_row)
        parameter_form.addRow("", self.replace_gpkg)
        parameter_form.addRow("", self.auto_export_excel)
        parameter_form.addRow("Archivo Excel", excel_row)
        parameter_form.addRow("", self.replace_excel)
        parameters.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.section_tabs.addTab(
            self._make_section_page(parameters),
            "2. Parámetros",
        )
        self.section_tabs.setTabToolTip(1, "Parámetros de validación y salida")

        group = QGroupBox("3. Controles gráficos a ejecutar")
        style_section(group, "#00C7CB")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(6, 6, 6, 5)
        group_layout.setSpacing(4)
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
        self.section_tabs.addTab(
            self._make_section_page(
                group,
                "Los grupos seleccionados se ejecutan sin modificar los datos de origen.",
            ),
            "3. Controles",
        )
        self.section_tabs.setTabToolTip(2, "Controles gráficos a ejecutar")
        try:
            saved_section = int(QgsSettings().value("control_calidad/active_setup_section", 0))
        except (TypeError, ValueError):
            saved_section = 0
        self.section_tabs.setCurrentIndex(max(0, min(saved_section, 2)))
        self.section_tabs.currentChanged.connect(
            lambda index: QgsSettings().setValue("control_calidad/active_setup_section", index)
        )

        setup_controls = QHBoxLayout()
        self.spatial_stats_button = QPushButton("Ver estadísticas espaciales")
        self.spatial_stats_button.setToolTip("Cuenta los elementos de las capas espaciales del esquema antes de validar.")
        self.spatial_stats_button.clicked.connect(self.show_spatial_statistics)
        setup_controls.addWidget(self.spatial_stats_button)
        setup_controls.addStretch()
        self.run_button = QPushButton("Ejecutar validación")
        self.run_button.setStyleSheet("background: #0468A3; color: white; font-weight: 700; padding: 9px 18px;")
        self.run_button.clicked.connect(self.run_rules)
        setup_controls.addWidget(self.run_button)
        setup_page_layout.addLayout(setup_controls)
        self.tabs.addTab(setup_page, "1. Conexión y validaciones")

        results_page = QWidget()
        results_page_layout = QVBoxLayout(results_page)
        results_page_layout.setContentsMargins(10, 10, 10, 10)
        result_box = QGroupBox("Avance del proceso y resultados")
        style_section(result_box, "#3FA4F5")
        result_layout = QVBoxLayout(result_box)
        self.summary = QLabel("Aún no se han ejecutado controles.")
        result_layout.addWidget(self.summary)
        self.location_summary = QLabel("Ubicación territorial: se identificará al ejecutar los controles.")
        self.location_summary.setWordWrap(True)
        self.location_summary.setStyleSheet("color: #0468A3; font-weight: 600; background: #E2F7F8; border-radius: 4px; padding: 5px;")
        result_layout.addWidget(self.location_summary)
        self.live_progress = QLabel("Regla actual: pendiente de iniciar")
        self.live_progress.setWordWrap(True)
        self.live_progress.setStyleSheet(
            "color: #37474F; background: #F1F7FA; border: 1px solid #B8D7E8; "
            "border-radius: 4px; padding: 6px;"
        )
        result_layout.addWidget(self.live_progress)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Componente", "Reglas ejecutadas", "Hallazgos", "Errores técnicos"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("QTableWidget { background: white; gridline-color: #D7EAF7; border: 1px solid #3FA4F5; } "
                                 "QHeaderView::section { background: #068CBB; color: white; border: none; padding: 6px; font-weight: 700; } "
                                 "QTableWidget::item:selected { background: #BFEAF0; color: #575756; }")
        self.table.setMinimumHeight(160)
        result_layout.addWidget(self.table)
        results_page_layout.addWidget(result_box, 1)

        controls = QGridLayout()
        controls.setHorizontalSpacing(5)
        controls.setVerticalSpacing(4)
        self.progress = QProgressBar(self)
        self.progress.setVisible(False)
        self.progress.setMinimumWidth(120)
        controls.addWidget(self.progress, 0, 0)
        self.status = QLabel("Configure la conexión y seleccione los controles.")
        self.status.setWordWrap(True)
        controls.addWidget(self.status, 0, 1)
        self.export_button = QPushButton("Reporte detallado")
        self.export_button.setToolTip("Generar reporte detallado")
        self.export_button.clicked.connect(self.export_excel)
        self.load_layers_button = QPushButton("Cargar capas")
        self.load_layers_button.setEnabled(False)
        self.load_layers_button.setToolTip("Carga los hallazgos por ítem y las capas espaciales de la base validada en grupos separados.")
        self.load_layers_button.clicked.connect(lambda: self.load_error_layers(True))
        controls.addWidget(self.load_layers_button, 1, 0)
        controls.addWidget(self.export_button, 1, 1)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setToolTip("Solicitar la cancelación segura de la validación en curso")
        self.cancel_button.setStyleSheet("background: #B3261E; color: white; font-weight: 700;")
        self.cancel_button.clicked.connect(self.cancel_validation)
        controls.addWidget(self.cancel_button, 2, 0)
        back_button = QPushButton("Volver")
        back_button.setToolTip("Volver a conexión y validaciones")
        back_button.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        controls.addWidget(back_button, 2, 1)
        results_page_layout.addLayout(controls)
        self.tabs.addTab(results_page, "2. Avance y resultados")
        self.auto_export_gpkg.toggled.connect(self.toggle_gpkg_options)
        self.auto_export_excel.toggled.connect(self.toggle_excel_options)
        self.toggle_gpkg_options(False)
        self.toggle_excel_options(False)
        for combo in (self.connection_mode, self.qgis_connection, self.schema):
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(12)
            combo.setMinimumWidth(0)
        for widget in (connection, parameters, group):
            widget.setMinimumWidth(0)
        self.load_qgis_connections()
        self.change_connection_mode(self.connection_mode.currentIndex())
        self.update_ingestion_button()
        self._connect_section_summary_updates()
        self._refresh_section_headers()

    def _make_section_page(self, content, footer_text=None):
        """Presenta una sección en una sola columna dentro de la barra horizontal."""
        content.setTitle("")
        page = QWidget(self)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(5, 5, 5, 5)
        page_layout.setSpacing(4)
        page_layout.addWidget(content, 0, Qt.AlignTop)
        if footer_text:
            footer = QLabel(footer_text, page)
            footer.setWordWrap(True)
            footer.setMinimumWidth(0)
            footer.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            footer.setStyleSheet("color: #52666a; padding: 3px;")
            page_layout.addWidget(footer)
        page_layout.addStretch()
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        return scroll

    def _make_collapsible_section(self, content, key, title, default_expanded):
        """Crea una cabecera compacta que muestra u oculta el contenido completo."""
        wrapper = QWidget(self)
        wrapper.setMinimumWidth(0)
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(3)

        header = QToolButton(wrapper)
        header.setCheckable(True)
        header.setToolButtonStyle(Qt.ToolButtonTextOnly)
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setMinimumHeight(30)
        header.setStyleSheet(
            "QToolButton { background: #E2F7F8; color: #0468A3; border: 1px solid #00AFC2; "
            "border-radius: 5px; padding: 5px 8px; text-align: left; font-weight: 700; } "
            "QToolButton:hover { background: #CFF1F3; }"
        )
        setting_key = f"control_calidad/sections/{key}_expanded"
        saved = QgsSettings().value(setting_key, default_expanded, type=bool)
        header.setChecked(bool(saved))
        content.setTitle("")
        content.setVisible(bool(saved))
        wrapper_layout.addWidget(header)
        wrapper_layout.addWidget(content)

        if not hasattr(self, "_collapsible_sections"):
            self._collapsible_sections = {}
        self._collapsible_sections[key] = {
            "wrapper": wrapper, "header": header, "content": content,
            "title": title, "setting": setting_key,
        }
        header.toggled.connect(lambda expanded, section_key=key: self._toggle_section(section_key, expanded))
        return wrapper

    def _toggle_section(self, key, expanded):
        section = self._collapsible_sections[key]
        section["content"].setVisible(expanded)
        QgsSettings().setValue(section["setting"], bool(expanded))
        self._refresh_section_headers()
        section["wrapper"].updateGeometry()
        self.updateGeometry()

    def _section_summary(self, key):
        if key == "connection":
            schema = self.schema.currentText().strip() if hasattr(self, "schema") else ""
            return schema or "esquema pendiente"
        if key == "parameters":
            exports = []
            if self.auto_export_gpkg.isChecked():
                exports.append("GPKG")
            if self.auto_export_excel.isChecked():
                exports.append("Excel")
            export_text = "+".join(exports) if exports else "sin exportación"
            return f"capas temporales · tol. {self.geometry_tolerance.value():.4f} m · {export_text}"
        if key == "controls":
            selected = sum(1 for check in self.category_checks.values() if check.isChecked())
            total_rules = 0
            for name, start, end in GRAPHICAL_GROUPS:
                check = self.category_checks.get(name)
                if check is not None and check.isChecked():
                    total_rules += 8 if start == 0 else end - start + 1
            return f"{selected} grupos · {total_rules} reglas seleccionadas"
        return ""

    def _refresh_section_headers(self, *_):
        for key, section in getattr(self, "_collapsible_sections", {}).items():
            expanded = section["header"].isChecked()
            prefix = "▼" if expanded else "▶"
            text = f"{prefix}  {section['title']}"
            if not expanded:
                summary = self._section_summary(key)
                if summary:
                    text += f"  —  {summary}"
            section["header"].setText(text)
            section["header"].setToolTip("Ocultar sección" if expanded else "Mostrar sección")

    def _connect_section_summary_updates(self):
        self.schema.currentTextChanged.connect(self._refresh_section_headers)
        self.geometry_tolerance.valueChanged.connect(self._refresh_section_headers)
        self.auto_export_gpkg.toggled.connect(self._refresh_section_headers)
        self.auto_export_excel.toggled.connect(self._refresh_section_headers)
        for check in self.category_checks.values():
            check.toggled.connect(self._refresh_section_headers)

    def owning_dock(self):
        parent = self.parentWidget()
        while parent is not None:
            if isinstance(parent, QDockWidget):
                return parent
            parent = parent.parentWidget()
        return None

    def toggle_compact_view(self):
        compact = self.tabs.isVisible()
        self.tabs.setVisible(not compact)
        self.subtitle.setVisible(not compact)
        self.heading.setVisible(not compact)
        self.minimize_button.setVisible(not compact)
        self.compact_status.setVisible(compact)
        self.collapse_button.setText("Expandir" if compact else "Contraer")
        dock = self.owning_dock()
        if dock is not None:
            if compact:
                dock.setMinimumWidth(0)
                self.setMinimumWidth(0)
                if dock.isFloating():
                    dock.resize(360, 110)
                else:
                    window = dock.parentWidget()
                    if hasattr(window, "resizeDocks"):
                        area = window.dockWidgetArea(dock)
                        orientation = Qt.Horizontal if area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea) else Qt.Vertical
                        window.resizeDocks([dock], [300 if orientation == Qt.Horizontal else 110], orientation)
            else:
                dock.setMinimumWidth(420)
                if dock.isFloating():
                    dock.resize(max(420, dock.width()), 560)
                else:
                    window = dock.parentWidget()
                    if hasattr(window, "resizeDocks"):
                        area = window.dockWidgetArea(dock)
                        orientation = Qt.Horizontal if area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea) else Qt.Vertical
                        window.resizeDocks([dock], [420 if orientation == Qt.Horizontal else 560], orientation)

    def minimize_panel(self):
        dock = self.owning_dock()
        if dock is None:
            self.showMinimized()
        elif dock.isFloating():
            dock.showMinimized()
        else:
            dock.hide()

    def update_ingestion_button(self, *_):
        visible = self.model.currentText() == "CICA"
        self.ingestion_label.setVisible(visible)
        self.ingestion_button.setVisible(visible)

    def toggle_gpkg_options(self, enabled):
        self.gpkg_path.setEnabled(enabled)
        self.gpkg_button.setEnabled(enabled)
        self.replace_gpkg.setEnabled(enabled)

    def toggle_excel_options(self, enabled):
        self.excel_path.setEnabled(enabled)
        self.excel_button.setEnabled(enabled)
        self.replace_excel.setEnabled(enabled)

    def choose_gpkg_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar GeoPackage", self.gpkg_path.text(), "GeoPackage (*.gpkg)")
        if path:
            self.gpkg_path.setText(path if path.lower().endswith(".gpkg") else path + ".gpkg")

    def choose_excel_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar resumen Excel", self.excel_path.text(), "Excel (*.xlsx)")
        if path:
            self.excel_path.setText(path if path.lower().endswith(".xlsx") else path + ".xlsx")

    def model_changed(self, *_):
        self.selected_sql_version = None
        self.repository_rules = []
        if hasattr(self, "sql_version_label"):
            self.sql_version_label.setText("Seleccione una versión de SQL")
        self.refresh_categories()
        self.open_sql_version_dialog()

    def repository_connection_params(self):
        return dict(REPOSITORY_CONNECTION)

    def repository_source(self, params):
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

    def open_sql_version_dialog(self):
        if psycopg2 is None:
            QMessageBox.warning(self, "Dependencia faltante", "No se puede consultar el repositorio SQL sin psycopg2.")
            return
        try:
            params = self.repository_connection_params()
            if params is None:
                return
            source = self.repository_source(params)
        except Exception as error:
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
                            f"SELECT componente, codigo_regla, tipo, sentencia_sql, COALESCE(descripcion_regla, '') FROM public.{table} "
                            "WHERE version = %s AND activa ORDER BY componente, orden, codigo_regla",
                            (version["id"]["version"],),
                        )
                    else:
                        cursor.execute(
                            f"SELECT componente, codigo_regla, tipo, sentencia_sql, COALESCE(descripcion, '') FROM {source['schema']}.reglas "
                            "WHERE version_id = %s AND activa ORDER BY componente, orden, codigo_regla",
                            (version["id"],),
                        )
                    self.repository_rules = [
                        {"component": row[0], "rule": row[1], "type": row[2], "sql": row[3], "description": row[4]}
                        for row in cursor.fetchall()
                    ]
            self.selected_sql_version = version
            self.sql_version_label.setText(f"{version['codigo']} · {len(self.repository_rules)} sentencias")
            self.refresh_categories()
            self.status.setText(f"Versión SQL seleccionada: {version['codigo']}.")
        except Exception as error:
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
        current_page = self.connection_stack.currentWidget()
        if current_page is not None:
            page_height = max(52, current_page.sizeHint().height())
            self.connection_stack.setMinimumHeight(page_height)
            self.connection_stack.setMaximumHeight(page_height)
        self.schema.clear()
        self.status.setText("Use Listar esquemas para consultar los esquemas disponibles.")

    def load_qgis_connections(self):
        settings = QgsSettings()
        settings.beginGroup("PostgreSQL/connections")
        names = sorted(
            name for name in settings.childGroups()
            if str(settings.value(f"{name}/host", "")).strip() == ALLOWED_POSTGRES_HOST
        )
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
            self.qgis_description.setText(
                f"No se encontraron conexiones guardadas para el servidor autorizado {ALLOWED_POSTGRES_HOST}."
            )
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
        self.populate_category_cards([
            (name, 8 if start == 0 else end - start + 1) for name, start, end in GRAPHICAL_GROUPS
        ])

    def populate_category_cards(self, categories):
        for index, (category_name, count) in enumerate(categories):
            card = QPushButton()
            card.setObjectName("categoryCard")
            card.setCheckable(True)
            card.setChecked(True)
            card.setIconSize(QSize(14, 14))
            card.setLayoutDirection(Qt.RightToLeft)
            card.setMinimumHeight(28)
            card.setStyleSheet(
                "QPushButton#categoryCard { background: #F7F9FA; color: #9AA3A8; border: 1px solid #D7E0E5; "
                "border-radius: 5px; text-align: left; padding: 3px 7px; font-weight: 600; } "
                "QPushButton#categoryCard:hover { background: #E2F7F8; color: #0468A3; border: 2px solid #3FA4F5; } "
                "QPushButton#categoryCard:checked { background: #0468A3; color: white; border: 2px solid #00C7CB; }"
            )
            self.update_category_card(card, category_name, count, True)
            card.toggled.connect(lambda checked, button=card, name=category_name, rules=count: self.update_category_card(button, name, rules, checked))
            card.toggled.connect(self.update_category_summary)
            card.toggled.connect(self._refresh_section_headers)
            self.category_checks[category_name] = card
            # Una regla por renglón evita recortes de texto y permite mantener
            # el panel lateral estrecho sin desplazamiento horizontal.
            self.category_cards.addWidget(card, index, 0)
        self.category_cards.setColumnStretch(0, 1)
        self.update_category_summary()

    @staticmethod
    def update_category_card(card, name, rules, checked):
        icon_name = "selected.svg" if checked else "unselected.svg"
        card.setIcon(QIcon(str(PLUGIN_DIR / "resources" / "icons" / icon_name)))
        card.setText(f"{name} · {rules} reglas")

    def select_all_categories(self):
        for action in self.category_checks.values():
            action.setChecked(True)
        self.update_category_summary()

    def update_category_summary(self, *_):
        selected = [name for name, action in self.category_checks.items() if action.isChecked()]
        count = sum(
            (8 if start == 0 else end - start + 1)
            for name, start, end in GRAPHICAL_GROUPS if name in selected
        )
        self.category_summary.setText(f"{len(selected)} grupos seleccionados · {count} reglas a ejecutar")
        self._refresh_section_headers()

    def connection_params(self):
        if self.connection_mode.currentIndex() == 0:
            params = self.qgis_connection_params()
        else:
            params = {"host": self.host.text().strip(), "port": self.port.text().strip(), "dbname": self.database.text().strip(), "user": self.user.text().strip(), "password": self.password.text()}
        if str(params.get("host", "")).strip() != ALLOWED_POSTGRES_HOST:
            raise ValueError(
                "Conexión no permitida. El Validador Consistencia Lógica Alfanumérica solamente puede conectarse "
                f"al servidor autorizado {ALLOWED_POSTGRES_HOST}."
            )
        return params

    def resolve_validation_context(self, params, schema):
        """Relaciona los cinco primeros dígitos del número predial con DIVIPOLA."""
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
                        "SELECT table_name, column_name FROM information_schema.columns "
                        "WHERE table_schema = %s "
                        "AND lower(column_name) IN ('numero_predial', 'numero_predial_nacional', 'npn') "
                        "ORDER BY CASE lower(table_name) "
                        "WHEN 'ilc_predio' THEN 1 WHEN 'lc_predio' THEN 2 WHEN 'cica_predio' THEN 3 ELSE 4 END, "
                        "table_name, column_name",
                        (schema,),
                    )
                    candidates = cursor.fetchall()
                    if not candidates:
                        return "Ubicación territorial no disponible: no se encontró un campo de número predial reconocido."
                    codes = set()
                    quoted_schema = '"' + schema.replace('"', '""') + '"'
                    for table, field in candidates:
                        quoted_table = '"' + table.replace('"', '""') + '"'
                        quoted_field = '"' + field.replace('"', '""') + '"'
                        cursor.execute(
                            f"SELECT DISTINCT left(trim({quoted_field}::text), 5) "
                            f"FROM {quoted_schema}.{quoted_table} "
                            f"WHERE {quoted_field} IS NOT NULL AND length(trim({quoted_field}::text)) >= 5"
                        )
                        codes.update(str(row[0]).zfill(5) for row in cursor.fetchall() if row[0])
                        if codes:
                            break
            codes = sorted(codes)
            matches = [(code, *divipola[code]) for code in codes if code in divipola]
            if not codes:
                return "Ubicación territorial no identificada: ILC_Predio no contiene números prediales válidos."
            if not matches:
                return "Ubicación territorial no identificada: los códigos DIVIPOLA no están en la referencia interna."
            labels = [f"{department} · {municipality} ({code})" for code, department, municipality in matches]
            visible = labels[:4]
            suffix = f" · y {len(labels) - len(visible)} más" if len(labels) > len(visible) else ""
            return "Departamento y municipio identificados: " + "; ".join(visible) + suffix
        except Exception as error:
            return "Ubicación territorial no disponible: " + re.sub(r"\s+", " ", str(error)).strip()[:160]

    def update_territorial_identification(self, *_):
        if not hasattr(self, "territory_label"):
            return
        schema = self.schema.currentText().strip()
        if not schema:
            self.territory_label.setText("Departamento y municipio: liste los esquemas y seleccione uno.")
            return
        try:
            context = self.resolve_validation_context(self.connection_params(), schema)
        except Exception as error:
            context = "Ubicación territorial no disponible: " + re.sub(r"\s+", " ", str(error)).strip()[:160]
        self.validation_context = context
        self.territory_label.setText(context)
        if hasattr(self, "location_summary"):
            self.location_summary.setText(context)

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
            self.schema.blockSignals(True)
            self.schema.clear()
            self.schema.addItems(schemas)
            if "public" in schemas:
                self.schema.setCurrentText("public")
            self.schema.blockSignals(False)
            self.status.setText("Conexión exitosa: " + version.split(",")[0])
            self.update_territorial_identification()
        except Exception as error:
            QMessageBox.critical(
                self,
                "No fue posible conectar",
                "El Validador Consistencia Lógica Alfanumérica solo permite validar bases de datos alojadas en el "
                f"servidor autorizado por la DTIC–IGAC: {ALLOWED_POSTGRES_HOST}.\n\n"
                "No fue posible establecer conexión con este servidor. Verifique que se "
                "encuentre conectado a la red institucional o a la VPN y que la conexión "
                "a PostgreSQL esté disponible.",
            )

    def show_spatial_statistics(self):
        if psycopg2 is None:
            QMessageBox.critical(self, "Dependencia faltante", "El QGIS instalado no incluye psycopg2.")
            return
        schema = self.schema.currentText().strip()
        if not schema:
            QMessageBox.information(
                self,
                "Seleccione un esquema",
                "Primero pruebe la conexión y seleccione el esquema que desea consultar.",
            )
            return
        try:
            params = self.connection_params()
        except Exception as error:
            QMessageBox.warning(self, "Conexión incompleta", str(error))
            return

        self.spatial_stats_button.setEnabled(False)
        self.status.setText(f"Calculando estadísticas espaciales de {schema}…")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        statistics = []
        failures = []
        try:
            with psycopg2.connect(**params, connect_timeout=8) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT f_table_name, f_geometry_column, type, srid "
                        "FROM geometry_columns WHERE f_table_schema = %s "
                        "ORDER BY f_table_name, f_geometry_column",
                        (schema,),
                    )
                    spatial_layers = cursor.fetchall()
                for index, (table, geometry_column, geometry_type, srid) in enumerate(spatial_layers, 1):
                    quoted_schema = '"' + schema.replace('"', '""') + '"'
                    quoted_table = '"' + table.replace('"', '""') + '"'
                    quoted_geometry = '"' + geometry_column.replace('"', '""') + '"'
                    query = (
                        f"SELECT count(*), count({quoted_geometry}), "
                        f"count(*) FILTER (WHERE {quoted_geometry} IS NULL), "
                        f"count(*) FILTER (WHERE {quoted_geometry} IS NOT NULL AND ST_IsEmpty({quoted_geometry})) "
                        f"FROM {quoted_schema}.{quoted_table}"
                    )
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SET LOCAL statement_timeout = '120s'")
                            cursor.execute(query)
                            total, with_geometry, null_count, empty_count = cursor.fetchone()
                        statistics.append({
                            "table": table,
                            "geometry_column": geometry_column,
                            "type": geometry_type,
                            "srid": srid,
                            "total": total,
                            "with_geometry": with_geometry,
                            "null": null_count,
                            "empty": empty_count,
                        })
                    except Exception as error:
                        connection.rollback()
                        error_detail = re.sub(r"\s+", " ", str(error)).strip()[:120]
                        failures.append(f"{table}: {error_detail}")
                    self.status.setText(f"Contando capa espacial {index} de {len(spatial_layers)}…")
                    QApplication.processEvents()
        except Exception as error:
            QMessageBox.critical(self, "No fue posible calcular estadísticas", str(error))
            return
        finally:
            QApplication.restoreOverrideCursor()
            self.spatial_stats_button.setEnabled(True)

        if not statistics:
            message = "El esquema seleccionado no contiene capas registradas en geometry_columns."
            if failures:
                message += "\n\nNo fue posible consultar:\n" + "\n".join(failures[:8])
            QMessageBox.information(self, "Sin capas espaciales", message)
            self.status.setText("No se encontraron capas espaciales para contabilizar.")
            return
        self.status.setText(f"Estadísticas calculadas para {len(statistics)} capas espaciales.")
        dialog = SpatialStatisticsDialog(self, schema, statistics)
        dialog.exec_()
        if failures:
            QMessageBox.warning(
                self,
                "Conteo parcial",
                f"Se mostraron {len(statistics)} capas. No fue posible contar {len(failures)} capas por permisos o tiempo de consulta.",
            )

    def run_rules(self):
        if psycopg2 is None:
            QMessageBox.critical(self, "Dependencia faltante", "El QGIS instalado no incluye psycopg2.")
            return
        selected = [name for name, check in self.category_checks.items() if check.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Seleccione controles", "Seleccione al menos una categoría de reglas.")
            return
        selected_layers = [
            item for item in LAYER_INFO
            if any(group in selected and start <= int(item[1]) <= end for group, start, end in GRAPHICAL_GROUPS)
        ]
        if "6. Validaciones complementarias" in selected:
            selected_layers.extend(COMPLEMENTARY_LAYER_INFO)
        validate_geometry = "0. Errores de geometría" in selected
        schema = self.schema.currentText().strip()
        if not schema:
            QMessageBox.warning(self, "Seleccione un esquema", "Pruebe la conexión y seleccione el esquema que desea validar.")
            return
        try:
            params = self.connection_params()
        except Exception as error:
            QMessageBox.warning(self, "Conexión incompleta", str(error))
            return
        # ``pg_temp`` dirige todas las tablas de procesamiento al esquema temporal
        # privado de esta sesión. Así no se requiere CREATE sobre la base ni se
        # conserva información al cerrar la conexión.
        output_schema = "pg_temp"
        temporary_output = True
        for enabled, path_text, replace, label in (
            (self.auto_export_gpkg.isChecked(), self.gpkg_path.text().strip(), self.replace_gpkg.isChecked(), "GeoPackage"),
            (self.auto_export_excel.isChecked(), self.excel_path.text().strip(), self.replace_excel.isChecked(), "Excel"),
        ):
            if enabled and not path_text:
                QMessageBox.warning(self, f"Archivo {label}", f"Seleccione el archivo de salida {label}.")
                return
            if enabled and Path(path_text).exists() and not replace:
                QMessageBox.warning(self, f"Archivo {label}", f"El archivo {label} ya existe. Active la opción de reemplazo o elija otro nombre.")
                return
        validation_context = self.resolve_validation_context(params, schema)
        try:
            with psycopg2.connect(**params, connect_timeout=8) as preview_connection:
                with preview_connection.cursor() as preview_cursor:
                    preview_cursor.execute(
                        "SELECT count(DISTINCT f_table_name) FROM geometry_columns WHERE f_table_schema=%s",
                        (schema,),
                    )
                    spatial_layer_count = int(preview_cursor.fetchone()[0])
        except Exception:
            spatial_layer_count = None
        selected_control_count = len(selected_layers) + (8 if validate_geometry else 0)
        output_items = ["capas temporales en QGIS"]
        if self.auto_export_gpkg.isChecked():
            output_items.append("GeoPackage")
        if self.auto_export_excel.isChecked():
            output_items.append("Excel")
        layer_text = str(spatial_layer_count) if spatial_layer_count is not None else "no disponible"
        confirmation = (
            f"Esquema: {schema}\n"
            f"Ubicación: {validation_context}\n"
            f"Grupos seleccionados: {len(selected)}\n"
            f"Reglas seleccionadas: {selected_control_count}\n"
            f"Capas espaciales disponibles: {layer_text}\n"
            f"Salida: {', '.join(output_items)}\n"
            f"Área mínima: {self.minimum_area.value():.6f} m²\n"
            f"Ancho mínimo: {self.minimum_width.value():.6f} m\n"
            f"Tolerancia geométrica: {self.geometry_tolerance.value():.4f} m"
        )
        answer = QMessageBox.question(
            self,
            "Confirmar validación",
            confirmation + "\n\n¿Desea iniciar la validación?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Yes,
        )
        if answer != QMessageBox.Yes:
            return
        self.clear_loaded_error_layers()
        # La ejecución y toda su retroalimentación se muestran en la segunda pestaña.
        self.tabs.setCurrentIndex(1)
        self.tabs.setTabText(1, "2. Avance y resultados · ejecutando")
        self.results.clear()
        self.table.setRowCount(0)
        self.load_layers_button.setEnabled(False)
        self.general_report_rows = []
        self.general_report_error = ""
        self.execution_failed = False
        self.execution_cancelled = False
        self.output_failed = False
        self.graphical_output_persistent = False
        self.validation_context = validation_context
        self.location_summary.setText(self.validation_context)
        self.expected_rule_count = selected_control_count
        self.current_activity = "Preparando consultas de validación"
        self.execution_started_at = datetime.now()
        self.execution_timer.start()
        self.update_live_progress()
        self.progress.setRange(0, selected_control_count * 2 + 2)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.status.setText(f"Ejecutando {selected_control_count} controles gráficos…")
        self.compact_status.setText("Validando · 0%")
        self.run_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.thread = QThread(self)
        self.worker = GraphicalRuleWorker(
            params, schema, output_schema, selected_layers,
            self.maximum_e_area.value(), self.minimum_area.value(), self.geometry_tolerance.value(),
            True, temporary_output, validate_geometry,
            self.minimum_width.value(), self.exclude_micro_errors.isChecked(),
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.add_result)
        self.worker.progress.connect(self.set_progress)
        self.worker.activity.connect(self.set_activity)
        self.worker.cancelled.connect(self.handle_cancelled)
        self.worker.fatal_error.connect(self.handle_fatal_error)
        self.worker.finished.connect(self.finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def add_result(self, result):
        self.results.append(result)
        self.update_live_progress()

    def set_activity(self, label, _current, _total):
        self.current_activity = label or "Procesando validación"
        self.update_live_progress()

    def update_live_progress(self):
        completed = len(self.results)
        pending = max(self.expected_rule_count - completed, 0)
        findings = sum(
            result.findings for result in self.results
            if isinstance(result.findings, int)
        )
        elapsed_seconds = 0
        if self.execution_started_at is not None:
            elapsed_seconds = max(0, int((datetime.now() - self.execution_started_at).total_seconds()))
        minutes, seconds = divmod(elapsed_seconds, 60)
        self.live_progress.setText(
            f"Regla actual: {self.current_activity}\n"
            f"Completadas: {completed}/{self.expected_rule_count} · Pendientes: {pending} · "
            f"Hallazgos acumulados: {findings} · Tiempo: {minutes:02d}:{seconds:02d}"
        )

    def cancel_validation(self):
        if self.worker is None or self.thread is None or not self.thread.isRunning():
            return
        answer = QMessageBox.question(
            self,
            "Cancelar validación",
            "¿Desea cancelar la validación en curso? Los resultados ya calculados se conservarán en memoria.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self.cancel_button.setEnabled(False)
        self.status.setText("Solicitando cancelación segura…")
        self.current_activity = "Cancelando la consulta activa"
        self.update_live_progress()
        self.worker.request_cancel()

    def handle_cancelled(self):
        self.execution_cancelled = True
        self.current_activity = "Cancelada por el usuario"
        self.compact_status.setText("Cancelada")
        self.update_live_progress()

    def handle_fatal_error(self, text):
        self.execution_failed = True
        self.current_activity = "Error técnico"
        self.compact_status.setText("Error en la validación")
        QMessageBox.critical(self, "No fue posible ejecutar", text)

    def add_general_report(self, rows, error):
        self.general_report_rows = rows
        self.general_report_error = error

    def set_progress(self, current, total):
        self.progress.setRange(0, total)
        self.progress.setValue(current)
        self.status.setText(f"Procesando etapa técnica {current} de {total}…")
        percentage = round((current / total) * 100) if total else 0
        self.compact_status.setText(f"Validando · {percentage}%")
        self.update_live_progress()

    def populate_result_summary(self):
        errors = sum(result.status == "Error" for result in self.results)
        findings = sum(
            result.findings for result in self.results
            if isinstance(result.findings, int)
        )
        grouped = {}
        for result in self.results:
            group = grouped.setdefault(result.category, {"rules": 0, "findings": 0, "errors": 0})
            group["rules"] += 1
            group["findings"] += result.findings if isinstance(result.findings, int) else 0
            group["errors"] += result.status == "Error"
        self.table.setRowCount(0)
        for category, values in sorted(grouped.items()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, value in enumerate((category, values["rules"], values["findings"], values["errors"])):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        return errors, findings

    def finished(self):
        self.execution_timer.stop()
        self.run_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.load_layers_button.setEnabled(bool(self.results))
        self.tabs.setCurrentIndex(1)
        self.tabs.setTabText(1, "2. Avance y resultados")
        errors, findings = self.populate_result_summary()
        if self.execution_failed:
            self.status.setText("Fallida por error técnico.")
            self.summary.setText(
                f"Fallida por error técnico · {len(self.results)} reglas alcanzadas · {findings} hallazgos acumulados"
            )
            self.update_live_progress()
            return
        if self.execution_cancelled:
            self.status.setText("Cancelada por el usuario.")
            self.summary.setText(
                f"Cancelada por el usuario · {len(self.results)} reglas completadas · {findings} hallazgos acumulados"
            )
            self.update_live_progress()
            return
        self.progress.setValue(self.progress.maximum())
        if errors:
            final_state = "Completada parcialmente"
        elif findings:
            final_state = "Completada con hallazgos"
        else:
            final_state = "Completada sin hallazgos"
        self.status.setText(final_state + ".")
        self.compact_status.setText(f"{final_state} · {findings} hallazgos")
        self.summary.setText(
            f"{final_state} · {len(self.results)} reglas ejecutadas · "
            f"{findings} hallazgos · {errors} errores técnicos"
        )
        self.current_activity = final_state
        self.update_live_progress()
        self.process_configured_outputs()
        if self.output_failed:
            self.status.setText("Completada parcialmente: una salida configurada no pudo generarse.")
            self.summary.setText(
                f"Completada parcialmente · {len(self.results)} reglas ejecutadas · "
                f"{findings} hallazgos · salida incompleta"
            )
            self.compact_status.setText("Completada parcialmente")

    def clear_loaded_error_layers(self):
        """Retira únicamente los grupos de resultados creados por este complemento."""
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        for node in list(root.children()):
            if isinstance(node, QgsLayerTreeGroup) and node.customProperty(self.loaded_error_group_key, False):
                layer_ids = [layer_node.layerId() for layer_node in node.findLayers()]
                if layer_ids:
                    project.removeMapLayers(layer_ids)
                if node.parent() is not None:
                    node.parent().removeChildNode(node)

    @staticmethod
    def geometry_from_value(value):
        if value is None:
            return None
        if isinstance(value, QgsGeometry):
            return QgsGeometry(value)
        raw = bytes(value) if isinstance(value, (bytes, bytearray, memoryview)) else None
        if raw is not None:
            geometry = QgsGeometry()
            geometry.fromWkb(raw)
            return geometry if not geometry.isNull() else None
        if not isinstance(value, str):
            return None
        text = value.strip()
        if not text:
            return None
        if text.upper().startswith("SRID=") and ";" in text:
            text = text.split(";", 1)[1]
        if text.startswith("\\x"):
            text = text[2:]
        if re.fullmatch(r"[0-9A-Fa-f]+", text) and len(text) % 2 == 0:
            try:
                geometry = QgsGeometry()
                geometry.fromWkb(bytes.fromhex(text))
                return geometry if not geometry.isNull() else None
            except ValueError:
                return None
        if re.match(r"^(POINT|MULTIPOINT|LINESTRING|MULTILINESTRING|POLYGON|MULTIPOLYGON|GEOMETRYCOLLECTION)\\s*", text, re.I):
            geometry = QgsGeometry.fromWkt(text)
            return geometry if not geometry.isNull() else None
        return None

    def result_geometry(self, row):
        preferred = [
            key for key in row
            if re.search(r"(^geom$|geometr|geom_|_geom|wkb)", str(key), re.I)
        ]
        preferred.sort(key=lambda key: 0 if str(key).lower() == "qgis_wkb" else 1)
        for key in preferred + [key for key in row if key not in preferred]:
            geometry = self.geometry_from_value(row.get(key))
            if geometry is not None:
                return key, geometry
        return None, None

    @staticmethod
    def result_domain(result):
        fields = " ".join(str(key) for row in (result.rows or [])[:5] for key in row)
        text = f"{result.category} {result.rule} {result.description} {fields}".lower()
        cartographic_markers = (
            "cc_", "av_", "vm_", "cartograf", "manzana", "vereda", "sector", "barrio",
            "perimetro", "límite", "limite", "centropoblado", "corregimiento",
            "localidad", "zona_homogenea", "zonahomogenea",
        )
        return "3. Cartografía catastral" if any(marker in text for marker in cartographic_markers) else "2. Terreno - Unidades"

    @staticmethod
    def display_result_description(result):
        code = str(result.rule).lstrip("0") or "0"
        if code in CONTAINMENT_LAYER_NAMES:
            return CONTAINMENT_LAYER_NAMES[code]
        description = (result.description or "Error").strip()
        for prefix in ("Huecos en ", "Superposición entre ", "Superposición en "):
            if description.lower().startswith(prefix.lower()):
                description = description[len(prefix):]
                break
        replacements = (
            ("LC_UnidadConstruccion", "CR_UnidadConstruccion"),
            ("LC_Construccion", "CR_Construccion"),
            ("LC_Terreno", "CR_Terreno"),
            ("lc_unidadconstruccion", "CR_UnidadConstruccion"),
            ("lc_construccion", "CR_Construccion"),
            ("lc_terreno", "CR_Terreno"),
        )
        for old, new in replacements:
            description = re.sub(re.escape(old), new, description, flags=re.I)
        return description

    def validation_crs(self):
        try:
            with psycopg2.connect(**self.connection_params(), connect_timeout=8) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT srid FROM geometry_columns WHERE f_table_schema = %s AND srid > 0 "
                        "GROUP BY srid ORDER BY count(*) DESC LIMIT 1",
                        (self.schema.currentText().strip(),),
                    )
                    row = cursor.fetchone()
            if row:
                return f"EPSG:{row[0]}"
        except Exception:
            pass
        project_crs = QgsProject.instance().crs()
        return project_crs.authid() if project_crs.isValid() else "EPSG:9377"

    def nonspatial_layer_for_result(self, result):
        if not result.rows:
            return None
        layer_name = f"{result.rule}. {self.display_result_description(result)} ({len(result.rows)})"
        layer = QgsVectorLayer("None", layer_name, "memory")
        if not layer.isValid():
            return None
        attribute_names = []
        for row in result.rows:
            for key in row:
                if re.search(r"(^geom$|geometr|geom_|_geom|wkb)", str(key), re.I):
                    continue
                if key not in attribute_names:
                    attribute_names.append(key)
        fields = [QgsField("regla", QVariant.String), QgsField("componente", QVariant.String)]
        used_names = {"regla", "componente"}
        field_map = []
        for original in attribute_names:
            clean = re.sub(r"[^A-Za-z0-9_]", "_", str(original))[:54] or "atributo"
            # GeoPackage reserva ``fid`` para su clave primaria entera. Los
            # resultados transitorios pueden traerlo como texto, por lo que se
            # conserva con un nombre no reservado durante la exportación.
            if clean.lower() == "fid":
                clean = "id_hallazgo"
            candidate = clean
            suffix = 2
            while candidate.lower() in used_names:
                candidate = f"{clean[:50]}_{suffix}"
                suffix += 1
            used_names.add(candidate.lower())
            field_map.append((original, candidate))
            fields.append(QgsField(candidate, QVariant.String))
        provider = layer.dataProvider()
        provider.addAttributes(fields)
        layer.updateFields()
        features = []
        for row in result.rows:
            feature = QgsFeature(layer.fields())
            values = [result.rule, result.category]
            values.extend("" if row.get(original) is None else str(row.get(original)) for original, _ in field_map)
            feature.setAttributes(values)
            features.append(feature)
        provider.addFeatures(features)
        return layer

    def memory_layer_for_result(self, result, crs_authid):
        spatial_rows = []
        geometry_key = None
        geometry_type = None
        for row in result.rows or []:
            key, geometry = self.result_geometry(row)
            if geometry is None:
                continue
            if (
                result.category != "0. Errores de geometría"
                and geometry.type() == QgsWkbTypes.PolygonGeometry
                and geometry.area() < self.minimum_area.value()
            ):
                continue
            if geometry_type is None:
                geometry_type = geometry.type()
                geometry_key = key
            if geometry.type() == geometry_type:
                spatial_rows.append((row, key, geometry))
        if not spatial_rows:
            return self.nonspatial_layer_for_result(result)

        type_name = {0: "Point", 1: "LineString", 2: "Polygon"}.get(geometry_type, "GeometryCollection")
        short_description = self.display_result_description(result)
        layer_name = f"{result.rule}. {short_description} ({len(spatial_rows)})"
        layer = QgsVectorLayer(f"{type_name}?crs={crs_authid}", layer_name, "memory")
        if not layer.isValid():
            return None

        attribute_names = []
        for row, row_geometry_key, _ in spatial_rows:
            for key in row:
                # No trasladar al atributo ni el WKB auxiliar ni otras copias de
                # geometría que PostGIS haya devuelto como texto hexadecimal.
                is_geometry_field = bool(
                    re.search(r"(^geom$|geometr|geom_|_geom|wkb)", str(key), re.I)
                )
                if key != row_geometry_key and not is_geometry_field and key not in attribute_names:
                    attribute_names.append(key)
        fields = [QgsField("regla", QVariant.String), QgsField("componente", QVariant.String)]
        used_names = {"regla", "componente"}
        field_map = []
        for original in attribute_names:
            clean = re.sub(r"[^A-Za-z0-9_]", "_", str(original))[:54] or "atributo"
            if clean.lower() == "fid":
                clean = "id_hallazgo"
            candidate = clean
            suffix = 2
            while candidate.lower() in used_names:
                candidate = f"{clean[:50]}_{suffix}"
                suffix += 1
            used_names.add(candidate.lower())
            field_map.append((original, candidate))
            fields.append(QgsField(candidate, QVariant.String))
        provider = layer.dataProvider()
        provider.addAttributes(fields)
        layer.updateFields()

        features = []
        for row, _, geometry in spatial_rows:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(geometry)
            values = [result.rule, result.category]
            values.extend("" if row.get(original) is None else str(row.get(original)) for original, _ in field_map)
            feature.setAttributes(values)
            features.append(feature)
        provider.addFeatures(features)
        layer.updateExtents()

        fill_color, border_color = ERROR_GROUP_STYLES.get(
            result.category, (QColor(235, 58, 70, 100), QColor(160, 0, 20))
        )
        symbol = layer.renderer().symbol()
        symbol.setColor(fill_color)
        if geometry_type == QgsWkbTypes.PolygonGeometry and symbol.symbolLayerCount():
            symbol_layer = symbol.symbolLayer(0)
            symbol_layer.setStrokeColor(border_color)
            symbol_layer.setStrokeWidth(1.1)
        elif geometry_type == QgsWkbTypes.LineGeometry:
            symbol.setColor(border_color)
            symbol.setWidth(1.5)
        elif geometry_type == QgsWkbTypes.PointGeometry:
            symbol.setColor(border_color)
            symbol.setSize(3.8)
        return layer

    @staticmethod
    def source_layer_section(table_name):
        name = table_name.lower().replace("_", "")
        if table_name.lower().startswith(("av_", "vm_")):
            return "C. Avalúos", "Avalúos"
        if table_name.lower().startswith("cc_"):
            return "B. Cartografía catastral", "Cartografía"
        if "unidadconstruccion" in name or "construccion" in name:
            return "A. Información predial", "1. Unidades de construcción"
        if "terreno" in name:
            return "A. Información predial", "2. Terrenos"
        if "direccion" in name:
            return "A. Información predial", "3. Dirección"
        return None, None

    @staticmethod
    def style_source_layer(layer, section, subtype, color_index=0):
        palettes = {
            "A. Información predial": ("#1864AB", "#2B8A3E", "#7048E8", "#495057"),
            "B. Cartografía catastral": ("#495057", "#087F5B", "#0B7285", "#5F3DC4", "#A61E4D", "#E67700"),
            "C. Avalúos": ("#862E9C", "#C2255C", "#5F3DC4", "#9C36B5"),
        }
        palette = palettes.get(section, ("#495057",))
        color = QColor(palette[color_index % len(palette)])
        symbol = layer.renderer().symbol()
        geometry_type = layer.geometryType()
        if geometry_type == QgsWkbTypes.PolygonGeometry and symbol.symbolLayerCount():
            symbol.setColor(QColor(color.red(), color.green(), color.blue(), 0))
            symbol_layer = symbol.symbolLayer(0)
            if hasattr(symbol_layer, "setFillColor"):
                symbol_layer.setFillColor(QColor(0, 0, 0, 0))
            symbol_layer.setStrokeColor(color)
            symbol_layer.setStrokeWidth(0.45)
        elif geometry_type == QgsWkbTypes.LineGeometry:
            symbol.setColor(color)
            symbol.setWidth(0.65)
        elif geometry_type == QgsWkbTypes.PointGeometry:
            symbol.setColor(color)
            symbol.setSize(2.4)
        layer.setOpacity(0.82)

    def load_source_layers(self, source_root):
        params = self.connection_params()
        schema = self.schema.currentText().strip()
        with psycopg2.connect(**params, connect_timeout=8) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT f_table_name, f_geometry_column, srid FROM geometry_columns "
                    "WHERE f_table_schema = %s ORDER BY f_table_name, f_geometry_column",
                    (schema,),
                )
                spatial_layers = cursor.fetchall()

        project = QgsProject.instance()
        section_groups = {}
        counters = defaultdict(int)
        loaded = 0
        for table, geometry_column, _srid in spatial_layers:
            section, subtype = self.source_layer_section(table)
            if section is None:
                continue
            uri = QgsDataSourceUri()
            uri.setConnection(
                str(params.get("host", "")), str(params.get("port", "5432")),
                str(params.get("dbname", "")), str(params.get("user", "")),
                str(params.get("password", "")),
            )
            uri.setDataSource(schema, table, geometry_column, "", "")
            display_name = f"{subtype} · {table}"
            layer = QgsVectorLayer(uri.uri(False), display_name, "postgres")
            if not layer.isValid():
                continue
            group = section_groups.get(section)
            if group is None:
                group = source_root.addGroup(section)
                section_groups[section] = group
            self.style_source_layer(layer, section, subtype, counters[section])
            counters[section] += 1
            project.addMapLayer(layer, False)
            layer_node = group.addLayer(layer)
            layer_node.setItemVisibilityChecked(True)
            group.setItemVisibilityChecked(True)
            group.setExpanded(True)
            loaded += 1
        return loaded

    def zoom_to_error_layer(self, layer, layer_node):
        """Acerca el mapa cuando el usuario activa una capa de hallazgos."""
        if self.iface is None or not layer_node.itemVisibilityChecked() or not layer.isValid():
            return
        extent = layer.extent()
        if extent.isEmpty():
            return
        width = max(extent.width(), extent.height())
        margin = width * 0.08 if width > 0 else 1.0
        extent.grow(margin)
        self.iface.mapCanvas().setExtent(extent)
        self.iface.setActiveLayer(layer)
        self.iface.mapCanvas().refresh()

    def load_error_layers(self, show_message=True, include_source=True):
        if isinstance(show_message, bool) is False:
            show_message = True
        self.clear_loaded_error_layers()
        candidates = [
            result for result in self.results
            if isinstance(result.findings, int) and result.findings > 0 and result.rows
        ]
        project = QgsProject.instance()
        root_group = project.layerTreeRoot().insertGroup(0, "Resultados de validación")
        root_group.setCustomProperty(self.loaded_error_group_key, True)
        errors_root = root_group.addGroup("Errores - Ítems")
        errors_root.setExpanded(False)
        category_groups = {}
        loaded = 0
        loaded_layers = []
        omitted = 0
        crs_authid = self.validation_crs()
        category_order = {name: index for index, (name, _start, _end) in enumerate(GRAPHICAL_GROUPS)}
        for result in sorted(candidates, key=lambda item: (category_order.get(item.category, 99), str(item.rule))):
            layer = self.memory_layer_for_result(result, crs_authid)
            if layer is None:
                omitted += 1
                continue
            category_group = category_groups.get(result.category)
            if category_group is None:
                category_group = errors_root.addGroup(result.category)
                category_group.setExpanded(False)
                category_groups[result.category] = category_group
            project.addMapLayer(layer, False)
            layer_node = category_group.addLayer(layer)
            layer_node.setItemVisibilityChecked(False)
            layer_node.visibilityChanged.connect(
                lambda *_args, current_layer=layer, current_node=layer_node:
                self.zoom_to_error_layer(current_layer, current_node)
            )
            loaded += 1
            loaded_layers.append(layer)
        if loaded == 0:
            root_group.removeChildNode(errors_root)

        source_loaded = 0
        if include_source:
            source_root = root_group.addGroup("Capas de la base validada")
            source_root.setItemVisibilityChecked(True)
            source_root.setExpanded(True)
            source_loaded = self.load_source_layers(source_root)
            if source_loaded == 0:
                root_group.removeChildNode(source_root)

        if loaded == 0 and source_loaded == 0:
            project.layerTreeRoot().removeChildNode(root_group)
        self.status.setText(
            f"{loaded} capas de error y {source_loaded} capas fuente cargadas · "
            f"{omitted} resultados sin geometría omitidos."
        )
        if show_message:
            QMessageBox.information(
                self,
                "Capas cargadas",
                f"Se cargaron {loaded} capas con hallazgos y {source_loaded} capas de la base validada. "
                f"Se omitieron {omitted} resultados que no incluyen geometría.",
            )
        return loaded_layers

    @staticmethod
    def safe_layer_name(name, used):
        base = re.sub(r"[^A-Za-z0-9_]", "_", name).strip("_").lower()[:52] or "error"
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base[:48]}_{suffix}"
            suffix += 1
        used.add(candidate)
        return candidate

    def export_layers_to_gpkg(self, layers, path):
        if not layers:
            raise ValueError("No hay resultados espaciales para exportar al GeoPackage.")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and self.replace_gpkg.isChecked():
            target.unlink()
        used = set()
        exported = 0
        failures = []
        for layer in layers:
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            exported_name = self.safe_layer_name(layer.name(), used)
            options.layerName = exported_name
            options.actionOnExistingFile = (
                QgsVectorFileWriter.CreateOrOverwriteFile if exported == 0
                else QgsVectorFileWriter.CreateOrOverwriteLayer
            )
            error, message, _new_file, _new_layer = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, str(target), QgsProject.instance().transformContext(), options
            )
            if error != QgsVectorFileWriter.NoError:
                failures.append(f"{layer.name()}: {message or 'error no especificado'}")
                continue
            exported += 1
            exported_layer = QgsVectorLayer(
                f"{target}|layername={exported_name}", layer.name(), "ogr"
            )
            if exported_layer.isValid() and layer.renderer() is not None:
                exported_layer.setRenderer(layer.renderer().clone())
                try:
                    exported_layer.saveStyleToDatabase(
                        "Validador Consistencia Lógica Alfanumérica", "Simbología del grupo de validación", True, ""
                    )
                except Exception:
                    # La capa ya fue exportada correctamente; algunos proveedores
                    # OGR antiguos no admiten la tabla de estilos del GeoPackage.
                    pass
        if exported == 0:
            raise RuntimeError("No fue posible exportar ninguna capa. " + " | ".join(failures[:5]))
        return exported, failures

    def process_configured_outputs(self):
        self.output_failed = False
        needs_layers = (
            self.auto_load_layers.isChecked()
            or self.auto_export_gpkg.isChecked()
        )
        layers = []
        try:
            if needs_layers:
                layers = self.load_error_layers(False, include_source=self.auto_load_layers.isChecked())
            completed = []
            output_warnings = []
            if self.auto_export_gpkg.isChecked():
                exported, failures = self.export_layers_to_gpkg(layers, self.gpkg_path.text().strip())
                completed.append("GeoPackage")
                if failures:
                    output_warnings.append(
                        f"GeoPackage: {exported} capas exportadas y {len(failures)} omitidas.\n\n" +
                        "\n".join(failures[:10])
                    )
            if self.auto_export_excel.isChecked():
                self.export_excel(self.excel_path.text().strip())
                completed.append("Excel")
            if not self.auto_load_layers.isChecked() and layers:
                self.clear_loaded_error_layers()
            if output_warnings:
                self.output_failed = True
                QMessageBox.warning(self, "Salida parcial", "\n\n".join(output_warnings))
        except Exception as error:
            self.output_failed = True
            self.status.setText("La validación terminó, pero falló una salida configurada.")
            QMessageBox.warning(self, "Salida incompleta", str(error))

    def export_excel(self, target_path=None):
        if isinstance(target_path, bool):
            target_path = None
        if not self.results:
            QMessageBox.information(self, "Sin resultados", "Ejecute controles antes de exportar un reporte.")
            return
        if target_path:
            target = Path(target_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            directory = str(target.parent)
        else:
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

        def excel_value(value):
            """Convierte valores de PostgreSQL a tipos aceptados por openpyxl."""
            if isinstance(value, memoryview):
                return value.tobytes().hex()
            if isinstance(value, (bytes, bytearray)):
                return bytes(value).hex()
            if isinstance(value, (list, tuple, set, dict)):
                return str(value)
            return value

        def is_geometry_field(key):
            return bool(re.search(r"(^geom$|geometr|geom_|_geom|wkb)", str(key), re.I))

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(target) if target_path else str(Path(directory) / f"resumen_control_calidad_{stamp}.xlsx")
        book = Workbook()
        summary = book.active
        summary.title = "Resumen ejecutivo"
        context = book.create_sheet("Contexto de validación", 0)
        context.append(["Ubicación territorial validada"])
        context.append([self.validation_context])
        summary.append(["Componente", "Reglas ejecutadas", "Hallazgos", "Errores técnicos"])
        grouped = defaultdict(lambda: {"rules": 0, "findings": 0, "errors": 0})
        for result in self.results:
            row = grouped[result.category]
            row["rules"] += 1
            row["findings"] += result.findings if isinstance(result.findings, int) else 0; row["errors"] += result.status == "Error"
            advance_report("Organizando resumen ejecutivo…")
        for category, values in sorted(grouped.items()):
            summary.append([category, values["rules"], values["findings"], values["errors"]])
        general = book.create_sheet("Reporte general")
        general.append(["ID", "Ítem evaluado", "Cantidad", "Reglas asociadas"])
        if self.general_report_rows:
            for item in self.general_report_rows:
                values = {str(key).lower(): value for key, value in item.items()}
                general.append([
                    excel_value(values.get("id", "")), excel_value(values.get("descripcion", "")),
                    excel_value(values.get("cantidad", "")),
                    excel_value(values.get("reglas_validacion_afectadas", "")),
                ])
        else:
            general.append(["", "No fue posible generar el reporte general", "", self.general_report_error or "No se recibieron resultados."])
        detail = book.create_sheet("Detalle de errores")
        detail.append(["Componente", "Regla incumplida", "Hallazgos", "Hoja de detalle"])
        error_rows = []
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
                if re.sub(r"[^a-z0-9]", "", str(key).lower()) != "numeropredialnacional"
                and not is_geometry_field(key)
            })
            condition_fields = [key for key in fields if str(key).lower().startswith("cond_")]
            fields = [key for key in fields if key not in condition_fields] + condition_fields
            rule_headers = [
                "Predio", *fields, "¿Es excepción?",
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
                    predio or "Sin identificador", *[excel_value(row.get(key, "")) for key in fields], "No",
                ], start=1):
                    rule_sheet.cell(index, column, value)
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
            if rule_sheet.max_row > 1:
                exception_validation = DataValidation(type="list", formula1='"Sí,No"', allow_blank=False)
                rule_sheet.add_data_validation(exception_validation)
                exception_column = rule_sheet.cell(4, rule_sheet.max_column).column_letter
                exception_validation.add(f"{exception_column}5:{exception_column}{rule_sheet.max_row}")
                rule_sheet.conditional_formatting.add(f"{exception_column}5:{exception_column}{rule_sheet.max_row}", FormulaRule(formula=[f'{exception_column}5="Sí"'], fill=exception))
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
                technical.append([result.category, result.rule, excel_value(result.detail)])
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
                if target.max_row > 1:
                    exception_validation = DataValidation(type="list", formula1='"Sí,No"', allow_blank=False)
                    target.add_data_validation(exception_validation)
                    exception_column = target.cell(4, target.max_column).column_letter
                    exception_validation.add(f"{exception_column}5:{exception_column}{target.max_row}")
                    target.conditional_formatting.add(f"{exception_column}5:{exception_column}{target.max_row}", FormulaRule(formula=[f'{exception_column}5="Sí"'], fill=exception))
            package_index.freeze_panes = "A2"; package_index.auto_filter.ref = package_index.dimensions
            for column in package_index.columns:
                package_index.column_dimensions[column[0].column_letter].width = min(max(len(str(cell.value or "")) for cell in column) + 2, 36)
            safe_category = re.sub(r"[^A-Za-z0-9_-]+", "_", category).strip("_") or "paquete"
            package.save(str(Path(directory) / f"detalle_{safe_category}_{stamp}.xlsx"))
            advance_report(f"Guardando paquete {category}…")
        for sheet in [detail, *[book[name] for name in rule_sheet_names.values()]]:
            book.remove(sheet)
        advance_report("Guardando reporte Excel…")
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
