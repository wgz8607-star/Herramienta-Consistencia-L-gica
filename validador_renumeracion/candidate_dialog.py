from qgis.PyQt.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QTreeWidget,QTreeWidgetItem,QMessageBox,QFileDialog
from openpyxl import Workbook
from .database import model_schemas,source_records
from .candidates import identify_candidates

HEADERS=['Número predial','DIVIPOLA','Zona','Prefijo 13','Manzana','Prefijo 17','Terreno','Tipo provisional','Condición','Clasificación']


class CandidateDialog(QDialog):
    def __init__(self,parent):
        super().__init__(parent);self.owner=parent;self.result=None;self.origin=''
        self.setWindowTitle('Predios a renumerar · CICA / Modelo Interno');self.resize(1150,740)
        layout=QVBoxLayout(self);form=QFormLayout();layout.addLayout(form)
        self.model=QComboBox();self.model.addItems(['CICA','Modelo Interno de Levantamiento 1.0']);form.addRow('Fuente',self.model)
        self.connection_mode=QComboBox();self.connection_mode.addItems(['Conexión guardada en QGIS','Conexión directa PostgreSQL']);form.addRow('Forma de conexión',self.connection_mode)
        self.connection=QComboBox()
        for index in range(parent.connection.count()):self.connection.addItem(parent.connection.itemText(index))
        self.connection.setCurrentText(parent.connection.currentText());form.addRow('Conexión QGIS',self.connection)
        self.connection_form=form
        self.direct={}
        for key,label in [('host','Servidor'),('port','Puerto'),('dbname','Base de datos'),('user','Usuario'),('password','Contraseña')]:
            field=QLineEdit();self.direct[key]=field
            if key=='password':field.setEchoMode(QLineEdit.Password)
            if key=='port':field.setText('5432')
            form.addRow(label,field);field.textChanged.connect(self.invalidate)
        self.connection_mode.currentIndexChanged.connect(self.connection_mode_changed)
        self.schema=QComboBox();self.list_button=QPushButton('Consultar esquemas del Modelo Interno');form.addRow('Esquema',self.schema);form.addRow(self.list_button)
        self.divipola=QLineEdit();self.divipola.setPlaceholderText('5 dígitos; vacío para todos los municipios');self.divipola.setMaxLength(5);form.addRow('Municipio · DIVIPOLA',self.divipola)
        note=QLabel('CICA: 7, 8 o 9 en posición 14 o 18. Modelo Interno: letra en posición 14 o 18. CICA: solo etapa VALIDADO y estado_control DESCARGADO_AL_SNC. Modelo Interno: sin filtro de etapa o estado. Las condiciones 8 y 9 (posición 22) quedan identificadas para revisión especial.');note.setWordWrap(True);layout.addWidget(note)
        self.read=QPushButton('Identificar predios a renumerar');layout.addWidget(self.read)
        self.status=QLabel('Seleccione la fuente y su conexión.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.tree=QTreeWidget();self.tree.setRootIsDecorated(False);self.tree.setHeaderLabels(HEADERS);layout.addWidget(self.tree,1)
        self.export=QPushButton('Exportar identificación a Excel');self.export.setEnabled(False);layout.addWidget(self.export)
        self.model.currentIndexChanged.connect(self.change_source);self.connection.currentTextChanged.connect(self.change_source)
        self.schema.currentTextChanged.connect(self.invalidate);self.divipola.textChanged.connect(self.invalidate)
        self.list_button.clicked.connect(self.list_schemas);self.read.clicked.connect(self.load);self.export.clicked.connect(self.save)
        self.change_source();self.connection_mode_changed()

    def invalidate(self,*_):
        self.result=None;self.tree.clear();self.export.setEnabled(False);self.status.setText('Fuente pendiente de consultar.')

    def change_source(self,*_):
        self.schema.clear();cica=self.model.currentText()=='CICA'
        if cica:self.schema.addItem('snc_cica_copy')
        self.schema.setEnabled(not cica);self.list_button.setEnabled(not cica);self.invalidate()

    def connection_mode_changed(self,*_):
        direct=self.connection_mode.currentIndex()==1
        self.connection.setEnabled(not direct)
        for field in self.direct.values():
            field.setVisible(direct)
        # Keep form labels in sync with their fields.
        form=self.connection_form
        for field in self.direct.values():
            label=form.labelForField(field)
            if label:label.setVisible(direct)
        self.change_source()

    def params(self):
        cica=self.model.currentText()=='CICA'
        if self.connection_mode.currentIndex()==0:
            return self.owner.params(preloaded=cica,connection_name=self.connection.currentText())
        params={key:(field.text() if key=='password' else field.text().strip()) for key,field in self.direct.items()}
        if cica:params['dbname']='sentencias'
        if not all(params[key] for key in ('host','port','dbname','user')):raise ValueError('Complete servidor, puerto, base de datos y usuario.')
        return params

    def run(self,function):
        self.setEnabled(False)
        try:return self.owner.task(function)
        finally:self.setEnabled(True)

    def list_schemas(self):
        try:
            params=self.params();self.invalidate();self.status.setText('Consultando esquemas…')
            schemas=self.run(lambda:model_schemas(params));self.schema.clear();self.schema.addItems(schemas)
            self.status.setText(f'{len(schemas)} esquemas con ILC_Predio disponibles.')
        except Exception as error:QMessageBox.warning(self,'No se consultaron los esquemas',str(error))

    def load(self):
        self.invalidate()
        try:
            code=self.divipola.text().strip()
            if code and (len(code)!=5 or not code.isascii() or not code.isdigit()):raise ValueError('Ingrese una DIVIPOLA de cinco dígitos.')
            model='CICA' if self.model.currentText()=='CICA' else 'Modelo Interno';schema=self.schema.currentText()
            if not schema:raise ValueError('Consulte y seleccione el esquema del Modelo Interno.')
            params=self.params();self.status.setText('Leyendo los predios de la fuente…')
            result=self.run(lambda:identify_candidates(source_records(params,model,schema,code),model))
            self.result=result;self.origin=f'{model} · {params.get("dbname",params.get("service",""))}.{schema} · DIVIPOLA: {code or "Todos"}'
            if model=='CICA':self.origin+=' · etapa=VALIDADO · estado_control=DESCARGADO_AL_SNC'
            for row in result['rows']:self.tree.addTopLevelItem(QTreeWidgetItem(list(row)))
            pending=sum(row[8] in '89' for row in result['rows'])
            self.status.setText(f'{self.origin}\nLeídos: {result["total"]} · NPN únicos válidos: {result["unique"]} · Provisionales: {len(result["rows"])} · Condición especial pendiente: {pending} · Duplicados excluidos: {result["duplicates"]} · Inválidos: {len(result["invalid"])}')
            self.export.setEnabled(True)
        except Exception as error:QMessageBox.warning(self,'No se identificaron los predios',str(error))

    def save(self):
        if self.result is None:return
        filename,_=QFileDialog.getSaveFileName(self,'Guardar identificación','predios_a_renumerar.xlsx','Excel (*.xlsx)')
        if not filename:return
        if not filename.lower().endswith('.xlsx'):filename+='.xlsx'
        try:
            book=Workbook();summary=book.active;summary.title='Resumen';summary.append(['Origen',self.origin]);summary.append(['Alcance','Identificación provisional; no aprueba ni ejecuta renumeraciones. Condiciones 8 y 9 pendientes.'])
            for key in ('total','unique','duplicates'):summary.append([key,self.result[key]])
            sheet=book.create_sheet('Provisionales');sheet.append(HEADERS)
            for row in self.result['rows']:sheet.append(row)
            invalid=book.create_sheet('No utilizados');invalid.append(['Fila de lectura','NPN','Motivo'])
            for row in self.result['invalid']:invalid.append(row)
            for sheet in book:
                sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
                for row in sheet:
                    for cell in row:
                        if isinstance(cell.value,str):cell.data_type='s'
            book.save(filename);book.close();self.status.setText('Exportado: '+filename)
        except Exception as error:QMessageBox.warning(self,'No se exportó',str(error))

    def reject(self):
        if not self.owner.busy:super().reject()

    def closeEvent(self,event):
        if self.owner.busy:event.ignore()
        else:event.accept()
