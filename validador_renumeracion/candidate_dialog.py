from qgis.PyQt.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QTreeWidget,QTreeWidgetItem,QMessageBox,QFileDialog,QCheckBox,QWidget,QHBoxLayout,QGroupBox
from openpyxl import Workbook
from .database import model_schemas,source_records,cica_municipalities,cica_copy_date,cica_zone_codes
from .candidates import identify_candidates

HEADERS=['Número predial','DIVIPOLA','Zona','Prefijo 13','Manzana','Prefijo 17','Terreno','Tipo provisional','Condición','Clasificación']


class CandidateDialog(QDialog):
    def __init__(self,parent,window_parent=None):
        super().__init__(parent if window_parent is None else window_parent);self.owner=parent;self.result=None;self.origin='';self.cica_codes=[];self.copy_date='Fecha de copia pendiente de consultar'
        self.setWindowTitle('Renumeración predial · Seleccionar fuente de datos');self.resize(1150,820)
        self.setStyleSheet('QDialog { background: #F3F6FA; } QLabel { color: #17324D; } QComboBox,QLineEdit { background: #FFFFFF; border: 1px solid #CDDFEF; border-radius: 4px; padding: 6px; } QPushButton { background: #0066B3; color: white; border-radius: 5px; padding: 8px 12px; } QPushButton:disabled { background: #E9ECEF; color: #7B8490; } QTreeWidget { background: white; alternate-background-color: #F3F8FC; border: 1px solid #D9E5EF; } QHeaderView::section { background: #0066B3; color: white; padding: 7px; }')
        layout=QVBoxLayout(self)
        title=QLabel('Seleccione la fuente de datos a revisar');title.setStyleSheet('font-size: 20px; font-weight: bold; color: #0066B3;');layout.addWidget(title)
        source_card=QGroupBox('1. Fuente de datos y alcance');source_card.setStyleSheet('QGroupBox { background: white; border: 1px solid #D9E5EF; border-radius: 8px; margin-top: 12px; padding: 14px; font-weight: bold; color: #0066B3; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }');form=QFormLayout(source_card);form.setSpacing(8);layout.addWidget(source_card)
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
        self.cica_lookup=QPushButton('Consultar departamentos y municipios CICA');form.addRow(self.cica_lookup)
        self.department=QComboBox();self.cica_municipality=QComboBox();form.addRow('Departamento',self.department);form.addRow('Municipio CICA',self.cica_municipality)
        self.copy_label=QLabel(self.copy_date);form.insertRow(1,'Fecha de la copia CICA',self.copy_label)
        self.copy_label.setStyleSheet('background: #E8F1FA; color: #0066B3; font-weight: bold; padding: 8px; border-left: 4px solid #0066B3;')
        self.cica_lookup.clicked.connect(self.load_cica_municipalities);self.department.currentIndexChanged.connect(self.update_cica_municipalities);self.cica_municipality.currentIndexChanged.connect(self.update_available_zones)
        self.zones_widget=QWidget();zone_layout=QHBoxLayout(self.zones_widget);zone_layout.setContentsMargins(0,0,0,0);self.zones={}
        for key,label in [('URBANO','Urbano'),('CP','Centro poblado (CP)'),('RURAL','Rural')]:
            checkbox=QCheckBox(label);checkbox.setChecked(True);checkbox.toggled.connect(self.invalidate);zone_layout.addWidget(checkbox);self.zones[key]=checkbox
        form.addRow('Zonas CICA',self.zones_widget)
        self.note=note=QLabel('CICA: 7, 8 o 9 en posición 14 o 18. Modelo Interno: letra en posición 14 o 18. CICA: solo etapa VALIDADO y estado_control DESCARGADO_AL_SNC. Modelo Interno: sin filtro de etapa o estado. Las condiciones 8 y 9 (posición 22) quedan identificadas para revisión especial.');note.setWordWrap(True);layout.addWidget(note)
        self.stats_button=QPushButton('Ver estadísticas CICA…');self.stats_button.clicked.connect(self.open_statistics);layout.addWidget(self.stats_button)
        self.read=QPushButton('Identificar predios a renumerar');layout.addWidget(self.read)
        self.status=QLabel('Seleccione la fuente y su conexión.');self.status.setWordWrap(True);layout.addWidget(self.status)
        results_title=QLabel('2. Predios identificados');results_title.setStyleSheet('color: #0066B3; font-size: 16px; font-weight: bold;');layout.addWidget(results_title)
        self.tree=QTreeWidget();self.tree.setAlternatingRowColors(True);self.tree.setRootIsDecorated(False);self.tree.setHeaderLabels(HEADERS);layout.addWidget(self.tree,1)
        self.export=QPushButton('Exportar identificación a Excel');self.export.setEnabled(False);layout.addWidget(self.export)
        self.r1_button=QPushButton('Consultar máximos del R1…');self.r1_button.clicked.connect(self.open_r1);layout.addWidget(self.r1_button)
        self.model.currentIndexChanged.connect(self.change_source);self.connection.currentTextChanged.connect(self.change_source)
        self.schema.currentTextChanged.connect(self.invalidate);self.divipola.textChanged.connect(self.invalidate)
        self.list_button.clicked.connect(self.list_schemas);self.read.clicked.connect(self.load);self.export.clicked.connect(self.save)
        self.change_source();self.connection_mode_changed();self.update_available_zones()

    def open_r1(self):
        try:
            params=self.params()
            if getattr(self.owner,'selected_source_params',None)!=params:
                self.owner.selected_source_params=dict(params);self.owner.tables.clear();self.owner.invalidate()
            if self.model.currentText()=='CICA':code=self.cica_municipality.currentData() or ''
            else:
                import re
                code=self.divipola.text().strip()
                if not code:
                    codes=set(re.findall(r'(?<![0-9])([0-9]{5})(?![0-9])',self.schema.currentText()))
                    code=next(iter(codes)) if len(codes)==1 else ''
            self.owner.set_source_municipality(code)
            self.owner.showNormal();self.owner.raise_();self.owner.activateWindow()
        except Exception as error:QMessageBox.warning(self,'Fuente pendiente',str(error))

    def invalidate(self,*_):
        self.result=None;self.tree.clear();self.export.setEnabled(False);self.status.setText('Fuente pendiente de consultar.')

    def change_source(self,*_):
        self.schema.clear();cica=self.model.currentText()=='CICA'
        for field in [self.connection_mode,self.connection,self.divipola]:
            field.setVisible(not cica);self.connection_form.labelForField(field).setVisible(not cica)
        for field in self.direct.values():
            visible=not cica and self.connection_mode.currentIndex()==1
            field.setVisible(visible);self.connection_form.labelForField(field).setVisible(visible)
        for field in [self.department,self.cica_municipality]:
            field.setVisible(cica);self.connection_form.labelForField(field).setVisible(cica)
        self.cica_lookup.setVisible(cica);self.list_button.setVisible(not cica)
        self.schema.setVisible(not cica);self.connection_form.labelForField(self.schema).setVisible(not cica)
        self.copy_label.setVisible(cica);self.connection_form.labelForField(self.copy_label).setVisible(cica)
        self.stats_button.setVisible(cica)
        self.note.setText(('CICA: provisionales 7, 8 o 9 en posición 14 o 18. Solo VALIDADO / DESCARGADO_AL_SNC.' if cica else 'Modelo Interno: letra en posición 14 o 18.')+' Condiciones 8 y 9 en posición 22: revisión especial pendiente.')
        if cica:self.schema.addItem('snc_cica_copy')
        self.schema.setEnabled(not cica);self.list_button.setEnabled(not cica);self.zones_widget.setVisible(cica);self.connection_form.labelForField(self.zones_widget).setVisible(cica);self.invalidate()

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
        if cica:
            from .repository import repository_params
            return repository_params()
        if self.connection_mode.currentIndex()==0:
            return self.owner.params(preloaded=cica,connection_name=self.connection.currentText())
        params={key:(field.text() if key=='password' else field.text().strip()) for key,field in self.direct.items()}
        if cica:params['dbname']='sentencias'
        if not all(params[key] for key in ('host','port','dbname','user')):raise ValueError('Complete servidor, puerto, base de datos y usuario.')
        return params

    def refresh_copy_date(self,params):
        try:
            value=self.run(lambda:cica_copy_date(params))
            self.copy_date=value.strftime('%d/%m/%Y %H:%M:%S') if value else 'Fecha no disponible'
            self.copy_label.setText(self.copy_date);self.copy_label.setToolTip('Último registro de public.copia_cica_progreso · inicio')
        except Exception as error:
            self.copy_date='Fecha no disponible';self.copy_label.setText(self.copy_date);self.copy_label.setToolTip(str(error))

    def update_available_zones(self,*_):
        self.invalidate()
        for checkbox in self.zones.values():
            checkbox.blockSignals(True);checkbox.setChecked(False);checkbox.hide();checkbox.blockSignals(False)
        code=self.cica_municipality.currentData()
        self.stats_button.setEnabled(bool(code))
        if not code:return
        try:
            params=self.params();codes=self.run(lambda:cica_zone_codes(params,code))
            available=set('RURAL' if code=='00' else 'URBANO' if code=='01' else 'CP' for code in codes if len(code)==2 and code.isdigit())
            for key,checkbox in self.zones.items():
                checkbox.setVisible(key in available);checkbox.setChecked(key in available)
            self.status.setText('Zonas disponibles para VALIDADO / DESCARGADO_AL_SNC: '+', '.join(sorted(available)))
        except Exception as error:
            QMessageBox.warning(self,'No se consultaron las zonas CICA',str(error))

    def open_statistics(self):
        from .cica_progress import CicaProgressDialog
        from .cica_statistics import read_cica_stages,read_detail
        code=self.cica_municipality.currentData()
        if not code:return
        params=self.params();label=self.cica_municipality.currentText()
        def loader():
            data=self.run(lambda:read_cica_stages(params,code,True))
            data.update(date=self.copy_date,municipality_label=label,detail_loader=lambda zone,cp,offset:self.run(lambda:read_detail(params,code,zone,cp,offset)))
            return data
        dialog=CicaProgressDialog(loader,self)
        dialog.note.setText('Estadísticas de todas las etapas del municipio. La identificación usa VALIDADO / DESCARGADO_AL_SNC.')
        dialog.exec_()

    def load_cica_municipalities(self):
        self.cica_codes=[];self.department.clear();self.cica_municipality.clear();self.invalidate()
        try:
            params=self.params();self.status.setText('Consultando municipios de la copia CICA…')
            codes=self.run(lambda:cica_municipalities(params));self.cica_codes=codes
            self.refresh_copy_date(params)
            self.department.clear();self.department.addItem('Todos los departamentos','')
            departments=sorted({self.owner.catalog.get(code,('Sin departamento identificado',''))[0] for code in codes})
            for name in departments:self.department.addItem(name,name)
            self.update_cica_municipalities();self.status.setText(f'{len(codes)} municipios disponibles en la copia CICA.')
        except Exception as error:QMessageBox.warning(self,'No se consultaron los municipios CICA',str(error))

    def update_cica_municipalities(self,*_):
        self.cica_municipality.clear();self.cica_municipality.addItem('Seleccione un municipio…',None)
        department=self.department.currentData() or ''
        for code in self.cica_codes:
            dep,name=self.owner.catalog.get(code,('Sin departamento identificado','Municipio no identificado'))
            if not department or dep==department:self.cica_municipality.addItem(f'{name} · {code}',code)
        self.invalidate()

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
            cica=self.model.currentText()=='CICA'
            code=(self.cica_municipality.currentData() or '') if cica else self.divipola.text().strip()
            if cica and not code:raise ValueError('Consulte y seleccione el departamento y municipio de la copia CICA.')
            if code and (len(code)!=5 or not code.isascii() or not code.isdigit()):raise ValueError('Ingrese una DIVIPOLA de cinco dígitos.')
            model='CICA' if self.model.currentText()=='CICA' else 'Modelo Interno';schema=self.schema.currentText()
            if not schema:raise ValueError('Consulte y seleccione el esquema del Modelo Interno.')
            zones=tuple(key for key,checkbox in self.zones.items() if checkbox.isChecked()) if model=='CICA' else None
            if model=='CICA' and not zones:raise ValueError('Seleccione al menos una zona para CICA.')
            params=self.params();self.status.setText('Leyendo los predios de la fuente…')
            result=self.run(lambda:identify_candidates(source_records(params,model,schema,code,zones),model))
            self.result=result;self.origin=f'{model} · {params.get("dbname",params.get("service",""))}.{schema} · DIVIPOLA: {code or "Todos"}'
            if model=='CICA':self.origin+=' · etapa=VALIDADO · estado_control=DESCARGADO_AL_SNC · Zonas: '+', '.join(zones)
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
