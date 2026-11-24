"""Review and compare a proposal. This module never writes to a database."""
from collections import Counter
from pathlib import Path
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QTreeWidget,QTreeWidgetItem,QTabWidget,QComboBox,QLineEdit,QFileDialog,QMessageBox)
from openpyxl import load_workbook,Workbook
from openpyxl.styles import Font,PatternFill
from .renumbering import read_comparison,compare_proposal

PROPOSAL_FIELDS=[('Provisional','old'),('Definitivo esperado','new'),('Resultado','status'),('Observación','reason'),('Base manzana/vereda R1','base_m'),('Base terreno R1','base_t'),('Grupo terreno (1–21)','family')]
COMPARE_FIELDS=[('Provisional','old'),('Definitivo esperado','expected'),('Definitivo del archivo','actual'),('Resultado','status'),('Observación','reason'),('Fila Excel','line')]


class ProposalDialog(QDialog):
    def __init__(self,proposal,context,parent):
        super().__init__(parent);self.proposal=proposal;self.context=context;self.file_rows=[];self.invalid_rows=[];self.comparison=[];self.filename=''
        self.setWindowTitle('3. Propuesta de renumeración y comparación');self.resize(1450,900)
        self.setWindowFlags(self.windowFlags()|Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint)
        self.setStyleSheet(parent.styleSheet())
        layout=QVBoxLayout(self)
        title=QLabel('3. Propuesta y comparación');title.setStyleSheet('font-size: 22px; color: #0066B3; font-weight: bold;');layout.addWidget(title)
        origin=QLabel(context);origin.setWordWrap(True);layout.addWidget(origin)
        note=QLabel('Propuesta de consulta: no modifica la base. Consecutivos sin saltos, en orden de provisionales. Excel de comparación: A = nuevo; B = provisional. Los pendientes no se aprueban. «Coincide» compara archivo y propuesta; no acredita cambios aplicados en la base.');note.setWordWrap(True);layout.addWidget(note)
        totals=Counter(row['status'] for row in proposal)
        self.summary=QLabel(f'Predios: {len(proposal)} · Generados: {totals["Generado"]} · Pendientes: {totals["Pendiente"]}');self.summary.setWordWrap(True);layout.addWidget(self.summary)
        row=QHBoxLayout();self.browse=QPushButton('Cargar archivo de renumeración…');self.browse.clicked.connect(self.choose_file);row.addWidget(self.browse)
        self.sheet=QComboBox();row.addWidget(self.sheet,1);self.compare_button=QPushButton('Comparar columnas A / B');self.compare_button.setEnabled(False);self.compare_button.clicked.connect(self.compare);row.addWidget(self.compare_button);layout.addLayout(row)
        self.file_status=QLabel('Archivo pendiente de cargar.');self.file_status.setWordWrap(True);layout.addWidget(self.file_status)
        row=QHBoxLayout();self.status_filter=QComboBox();self.status_filter.addItem('Todos los resultados','');self.search=QLineEdit();self.search.setPlaceholderText('Buscar NPN o prefijo…');row.addWidget(self.status_filter);row.addWidget(self.search,1);layout.addLayout(row)
        self.tabs=QTabWidget();self.views={}
        for name,fields in [('Propuesta',PROPOSAL_FIELDS),('Comparación',COMPARE_FIELDS)]:
            tree=QTreeWidget();tree.setRootIsDecorated(False);tree.setAlternatingRowColors(True);tree.setHeaderLabels([label for label,_ in fields]);self.tabs.addTab(tree,name);self.views[name]=tree
        self.invalid=QTreeWidget();self.invalid.setRootIsDecorated(False);self.invalid.setHeaderLabels(['Fila Excel','A · Nuevo','B · Provisional','Motivo']);self.tabs.addTab(self.invalid,'Filas no utilizadas');layout.addWidget(self.tabs,1)
        row=QHBoxLayout();export=QPushButton('Exportar propuesta y comparación');export.clicked.connect(self.export);row.addWidget(export);row.addStretch();close=QPushButton('Cerrar');close.clicked.connect(self.accept);row.addWidget(close);layout.addLayout(row)
        self.sheet.currentTextChanged.connect(self.clear_comparison);self.tabs.currentChanged.connect(self.update_filters);self.status_filter.currentIndexChanged.connect(self.render);self.search.textChanged.connect(self.render);self.update_filters()

    def clear_comparison(self,*_):
        self.comparison=[];self.file_rows=[];self.invalid_rows=[];self.invalid.clear()
        self.update_filters()
        if self.filename:self.file_status.setText(Path(self.filename).name+' · hoja '+self.sheet.currentText()+' · pendiente de comparar.')

    def update_filters(self,*_):
        data=self.comparison if self.tabs.currentIndex()==1 else self.proposal
        self.status_filter.blockSignals(True);self.status_filter.clear();self.status_filter.addItem('Todos los resultados','')
        for status in sorted({row['status'] for row in data}):self.status_filter.addItem(status,status)
        self.status_filter.blockSignals(False);self.render()

    def render(self,*_):
        from qgis.PyQt.QtGui import QColor
        selected=self.status_filter.currentData() or '';needle=self.search.text().strip().casefold()
        for index,(name,fields,data) in enumerate([('Propuesta',PROPOSAL_FIELDS,self.proposal),('Comparación',COMPARE_FIELDS,self.comparison)]):
            tree=self.views[name];tree.setUpdatesEnabled(False);tree.clear()
            for row in data:
                if selected and self.tabs.currentIndex()==index and row['status']!=selected:continue
                if needle and needle not in ' '.join(str(value) for value in row.values()).casefold():continue
                item=QTreeWidgetItem(['' if row.get(key) is None else str(row.get(key,'')) for _,key in fields])
                color='#217346' if row['status']=='Coincide' else '#BE594D' if row['status'] in ('Diferencia','Provisional duplicado en archivo','Definitivo duplicado en archivo') else '#9B6400' if 'Pendiente' in row['status'] or row['status']=='Falta en archivo' else '#17324D'
                for column in range(len(fields)):item.setForeground(column,QColor(color))
                tree.addTopLevelItem(item)
            for column in range(tree.columnCount()):tree.resizeColumnToContents(column)
            tree.setUpdatesEnabled(True)

    def choose_file(self):
        filename,_=QFileDialog.getOpenFileName(self,'Archivo de renumeración','','Excel (*.xlsx)')
        if not filename:return
        self.filename='';self.sheet.clear();self.comparison=[];self.file_rows=[];self.invalid_rows=[];self.invalid.clear();self.compare_button.setEnabled(False);self.file_status.setText('Archivo pendiente de cargar.');self.update_filters()
        try:
            book=load_workbook(filename,read_only=True,data_only=True)
            try:self.sheet.addItems(book.sheetnames)
            finally:book.close()
            self.filename=filename;self.compare_button.setEnabled(True);self.file_status.setText(Path(filename).name+' · seleccione hoja y compare A / B.')
        except Exception as error:QMessageBox.warning(self,'No se leyó el archivo',str(error))

    def compare(self):
        if not self.filename:return
        self.comparison=[];self.invalid_rows=[];self.invalid.clear()
        try:
            filename=self.filename;sheet=self.sheet.currentText()
            rows,invalid=self.parent().run(lambda:read_comparison(filename,sheet))
            self.file_rows=rows;self.invalid_rows=invalid;self.comparison=compare_proposal(self.proposal,rows)
            for row in invalid:self.invalid.addTopLevelItem(QTreeWidgetItem([str(value) for value in row]))
            counts=Counter(row['status'] for row in self.comparison)
            self.file_status.setText(Path(filename).name+' · hoja '+sheet+' · '+' · '.join(f'{key}: {count}' for key,count in sorted(counts.items()))+f' · Filas inválidas: {len(invalid)}')
            self.tabs.setCurrentIndex(1);self.update_filters()
        except Exception as error:
            self.file_status.setText('No se completó la comparación.');self.update_filters();QMessageBox.warning(self,'No se comparó el archivo',str(error))

    def export(self):
        filename,_=QFileDialog.getSaveFileName(self,'Exportar propuesta','propuesta_renumeracion.xlsx','Excel (*.xlsx)')
        if not filename:return
        if not filename.lower().endswith('.xlsx'):filename+='.xlsx'
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            book=Workbook();summary=book.active;summary.title='Resumen';summary.append(['Fecha de generación',datetime.now(ZoneInfo('America/Bogota')).isoformat(timespec='seconds')]);summary.append(['Contexto',self.context]);summary.append(['Archivo comparado',Path(self.filename).name+' · '+self.sheet.currentText() if self.filename else 'Sin archivo']);summary.append(['Alcance','Propuesta; no se modifican datos. Generado no equivale a cambio aplicado.'])
            for status,count in sorted(Counter(r['status'] for r in self.proposal).items()):summary.append([status,count])
            for status,count in sorted(Counter(r['status'] for r in self.comparison).items()):summary.append(['Comparación · '+status,count])
            sheet=book.create_sheet('Renumeracion');sheet.append(['Nuevo esperado','Provisional','Resultado','Observación'])
            for row in self.proposal:sheet.append([row['new'],row['old'],row['status'],row['reason']])
            audit=book.create_sheet('Bases R1');audit.append([label for label,_ in PROPOSAL_FIELDS])
            for row in self.proposal:audit.append([row.get(key) for _,key in PROPOSAL_FIELDS])
            sheet=book.create_sheet('Comparacion');sheet.append([label for label,_ in COMPARE_FIELDS])
            for row in self.comparison:sheet.append([row.get(key) for _,key in COMPARE_FIELDS])
            invalid=book.create_sheet('Filas no utilizadas');invalid.append(['Fila Excel','A · Nuevo','B · Provisional','Motivo'])
            for row in self.invalid_rows:invalid.append(row)
            for sheet in book:
                sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
                for cell in sheet[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='0066B3')
                for column in sheet.columns:sheet.column_dimensions[column[0].column_letter].width=36
                for row in sheet:
                    for cell in row:
                        if isinstance(cell.value,str):cell.data_type='s'
            book.save(filename);book.close();self.file_status.setText('Exportado: '+filename)
        except Exception as error:QMessageBox.warning(self,'No se exportó',str(error))
