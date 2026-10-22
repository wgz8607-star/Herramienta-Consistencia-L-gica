"""Formulario de preparación de insumos CICA para PostgreSQL/PostGIS."""
from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from qgis.PyQt.QtWidgets import (
    QDialog, QFileDialog, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)


CSV_INPUTS = {
    "Datos Contacto": "cica_contacto",
    "Datos Predio - Derecho": "cica_predio_derecho",
    "Predio": "cica_predio",
    "Datos Propietario": "cica_propietario",
    "Justificación": "cica_justificacion",
    "Seguimiento de Control": "cica_seguimiento_control",
    "Unidad de Construcción": "cica_unidad_construccion",
}


class CicaIngestionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ingesta de insumos CICA")
        self.resize(760, 620)
        self.files = {}
        layout = QVBoxLayout(self)
        title = QLabel("Ingesta CICA: archivos planos y geodatabase")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #08756a;")
        layout.addWidget(title)
        note = QLabel("Seleccione los siete CSV individualmente. La verificación comprueba que estén completos antes de cargar a PostgreSQL/PostGIS.")
        note.setWordWrap(True)
        layout.addWidget(note)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)
        for label, destination in CSV_INPUTS.items():
            field = QLineEdit()
            field.setReadOnly(True)
            button = QPushButton("Seleccionar")
            button.clicked.connect(lambda _=False, key=label: self.choose_csv(key))
            row = QHBoxLayout()
            row.addWidget(field, 1)
            row.addWidget(button)
            form.addRow(f"{label} → {destination}", row)
            self.files[label] = field
        self.gdb = QLineEdit()
        self.gdb.setReadOnly(True)
        choose_gdb = QPushButton("Seleccionar")
        choose_gdb.clicked.connect(self.choose_gdb)
        gdb_row = QHBoxLayout()
        gdb_row.addWidget(self.gdb, 1)
        gdb_row.addWidget(choose_gdb)
        form.addRow("Geodatabase CICA (.gdb o .zip)", gdb_row)
        self.schema = QLineEdit("cica_cargue")
        form.addRow("Nuevo esquema de destino", self.schema)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        self.status = QLabel("Seleccione los insumos requeridos.")
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        buttons.addStretch()
        validate = QPushButton("Validar insumos")
        validate.clicked.connect(self.validate_inputs)
        buttons.addWidget(validate)
        layout.addLayout(buttons)

    def choose_csv(self, key):
        path, _ = QFileDialog.getOpenFileName(self, f"Seleccione {key}", "", "Archivos CSV (*.csv)")
        if path:
            self.files[key].setText(path)

    def choose_gdb(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccione la geodatabase comprimida", "", "Archivo ZIP (*.zip)")
        if not path:
            path = QFileDialog.getExistingDirectory(self, "Seleccione la carpeta .gdb")
        if path:
            self.gdb.setText(path)

    def validate_inputs(self):
        missing = [label for label, field in self.files.items() if not field.text()]
        if missing:
            QMessageBox.warning(self, "Insumos incompletos", "Faltan: " + ", ".join(missing))
            return
        if not self.gdb.text():
            QMessageBox.warning(self, "Insumo incompleto", "Seleccione la geodatabase CICA.")
            return
        errors = []
        for label, field in self.files.items():
            try:
                with open(field.text(), "r", encoding="utf-8-sig", newline="") as stream:
                    header = next(csv.reader(stream), [])
                if not header or not any("predial" in value.lower() for value in header):
                    errors.append(label)
            except Exception:
                errors.append(label)
        gdb_path = Path(self.gdb.text())
        valid_gdb = (gdb_path.is_dir() and gdb_path.suffix.lower() == ".gdb")
        if gdb_path.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(gdb_path) as archive:
                    valid_gdb = any(entry.filename.lower().endswith(".gdb/") for entry in archive.infolist())
            except zipfile.BadZipFile:
                valid_gdb = False
        if not valid_gdb:
            errors.append("Geodatabase")
        if errors:
            QMessageBox.critical(self, "No se pudieron validar insumos", "Revise: " + ", ".join(errors))
            return
        self.status.setText("Insumos completos y válidos. Esquema de destino: " + self.schema.text().strip())
        QMessageBox.information(self, "Insumos validados", "Los 7 CSV y la geodatabase CICA están listos para cargar en el esquema indicado.")
