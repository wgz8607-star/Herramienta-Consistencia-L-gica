"""Record-level review viewer; filtering never changes the underlying case list."""
from collections import Counter
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout,
)
from .review import PENDING, STATES


class ReviewDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.current_case = None
        self.rendering = False
        self.setWindowTitle('Revisión de hallazgos por registro')
        self.resize(1120, 750)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('El seguimiento del usuario no modifica el resultado automático de la validación.'))
        context = owner.review_context
        self.context_label = QLabel(' · '.join(str(context.get(k, '')) for k in ('model', 'environment', 'database', 'schema')))
        self.context_label.setWordWrap(True)
        layout.addWidget(self.context_label)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Filtrar por validación, datos, estado u observación…')
        self.search.textChanged.connect(self.apply_filter)
        layout.addWidget(self.search)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.currentCellChanged.connect(self.select_case)
        layout.addWidget(self.table, 1)
        controls = QHBoxLayout()
        controls.addWidget(QLabel('Estado de revisión del usuario'))
        self.state = QComboBox()
        self.state.addItems(STATES)
        controls.addWidget(self.state)
        self.date = QLabel()
        controls.addWidget(self.date)
        layout.addLayout(controls)
        layout.addWidget(QLabel('Observación (obligatoria para Excepción)'))
        self.observation = QTextEdit()
        self.observation.setMaximumHeight(100)
        layout.addWidget(self.observation)
        actions = QHBoxLayout()
        apply = QPushButton('Aplicar seguimiento')
        apply.clicked.connect(self.commit_editor)
        actions.addWidget(apply)
        save = QPushButton('Guardar revisión en Excel')
        save.clicked.connect(owner.save_review_excel)
        actions.addWidget(save)
        recover = QPushButton('Recuperar revisión')
        recover.clicked.connect(owner.recover_review)
        actions.addWidget(recover)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self):
        self.rendering = True
        context = self.owner.review_context
        self.context_label.setText(' · '.join(str(context.get(k, '')) for k in ('model', 'environment', 'database', 'schema')))
        self.current_case = None
        self.table.clear()
        self.fields = sorted({str(k) for case in self.owner.review_cases for k in case.data})
        self.table.setColumnCount(7 + len(self.fields))
        self.table.setHorizontalHeaderLabels([
            'Componente', 'Validación', 'Resultado automático', 'Estado de revisión',
            'Observación', 'Fecha de revisión', 'Recuperación automática', *self.fields,
        ])
        self.table.setRowCount(len(self.owner.review_cases))
        from .review import display
        counts = Counter(case.key for case in self.owner.review_cases)
        for index, case in enumerate(self.owner.review_cases):
            recovery = 'No: identidad insuficiente' if not case.recoverable else ('No: caso duplicado' if counts[case.key] > 1 else 'Coincidencia única requerida')
            values = [case.component, case.rule, case.automatic, *case.tracking(), recovery,
                      *[display(case.data.get(k)) for k in self.fields]]
            for column, value in enumerate(values):
                self.table.setItem(index, column, QTableWidgetItem(str(value)))
        self.table.setCurrentCell(-1, -1)
        self.table.clearSelection()
        self.state.setCurrentText(PENDING)
        self.observation.clear()
        self.date.clear()
        self.state.setEnabled(False)
        self.observation.setEnabled(False)
        self.rendering = False
        self.apply_filter()

    def commit_editor(self):
        if self.current_case is None:
            return True
        case = self.owner.review_cases[self.current_case]
        try:
            changed = case.set_review(self.state.currentText(), self.observation.toPlainText())
        except ValueError as error:
            QMessageBox.warning(self, 'Revisión incompleta', str(error))
            return False
        if changed:
            self.owner.review_dirty = True
            for column, value in enumerate(case.tracking(), 3):
                self.table.setItem(self.current_case, column, QTableWidgetItem(value))
            self.date.setText(case.fecha_revision_usuario)
        return True

    def select_case(self, row, column, previous_row, previous_column):
        if self.rendering:
            return
        if not self.commit_editor():
            self.table.blockSignals(True)
            self.table.setCurrentCell(self.current_case, 0)
            self.table.blockSignals(False)
            return
        self.current_case = row if row >= 0 else None
        if self.current_case is not None:
            case = self.owner.review_cases[row]
            self.state.setCurrentText(case.estado_revision_usuario)
            self.observation.setPlainText(case.observacion_usuario)
            self.date.setText(case.fecha_revision_usuario)
        else:
            self.state.setCurrentText(PENDING)
            self.observation.clear()
            self.date.clear()
        self.state.setEnabled(self.current_case is not None)
        self.observation.setEnabled(self.current_case is not None)

    def apply_filter(self):
        if not self.commit_editor():
            return
        text = self.search.text().casefold()
        for row in range(self.table.rowCount()):
            values = ' '.join(self.table.item(row, col).text() for col in range(self.table.columnCount()))
            self.table.setRowHidden(row, text not in values.casefold())
        if self.current_case is not None and self.table.isRowHidden(self.current_case):
            self.table.setCurrentCell(-1, -1)
            self.table.clearSelection()

    def closeEvent(self, event):
        if not self.commit_editor() or not self.owner.confirm_review_changes():
            event.ignore()
            return
        event.accept()

    def reject(self):
        self.close()  # Escape must use the same unsaved-change guard.
