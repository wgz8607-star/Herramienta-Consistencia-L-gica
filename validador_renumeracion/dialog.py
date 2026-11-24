from pathlib import Path
from datetime import datetime
import re
from concurrent.futures import ThreadPoolExecutor
from queue import SimpleQueue
from qgis.core import QgsSettings,QgsApplication,QgsAuthMethodConfig
from qgis.PyQt.QtCore import Qt,QTimer,QEventLoop
from qgis.PyQt.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QWidget,QLabel,QComboBox,QLineEdit,QPushButton,QFileDialog,QMessageBox,QTreeWidget,QTreeWidgetItem,QTabWidget,QProgressBar,QInputDialog)
from .core import build_maxima,visible_rows,zone_name
from .readers import inspect_excel,file_records,municipality_catalog
from .database import list_tables,database_records
from .exporter import export_maxima,ZONE_FIELDS,PREFIX_FIELDS,BLOCK_FIELDS


class MaximaDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle('Renumeración predial · Máximos R1')
        self.setWindowFlags(self.windowFlags()|Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint)
        self.resize(1200,820)
        self.result=None;self.busy=False;self.origin='';self.header_row=1;self._passwords={}
        self.catalog=municipality_catalog(Path(__file__).parent/'resources/divipola.xlsx')
        self.setStyleSheet('QDialog { background: #F3F6FA; } QLabel { color: #17324D; } QPushButton { background: #0066B3; color: white; padding: 7px 11px; border-radius: 5px; } QPushButton:disabled { background: #E9ECEF; color: #7B8490; } QTreeWidget { background: white; alternate-background-color: #F3F8FC; } QHeaderView::section { background: #0066B3; color: white; padding: 6px; }')
        outer=QVBoxLayout(self)
        title=QLabel('Máximos de manzana y terreno del R1');title.setStyleSheet('font-size: 22px; font-weight: bold; color: #0066B3;');outer.addWidget(title)
        note=QLabel('Solo consulta. Manzana: posiciones 14–17; terreno: 18–21. Zona–sector: posiciones 6–9. El máximo de manzana se calcula por prefijo 1–13 y el de terreno por manzana completa 1–17.');note.setWordWrap(True);outer.addWidget(note)
        self.inputs=QWidget();form=QFormLayout(self.inputs);form.setContentsMargins(0,4,0,4)
        self.source_mode=QComboBox();self.source_mode.addItems(['Opción 1: Archivos r1 y r2 cargados por usuario','Opción 2: Archivos r1 y r2 precargados - Sin fecha seleccionada','Opción 3: Archivos r1 y r2 cargados en "Public" de la base seleccionada']);form.addRow('Origen del R1',self.source_mode)
        self.file_page=QWidget();file_form=QFormLayout(self.file_page);file_form.setContentsMargins(0,0,0,0)
        self.file=QLineEdit();self.file.setReadOnly(True);browse=QPushButton('Seleccionar R1…');browse.clicked.connect(self.choose_file)
        row=QHBoxLayout();row.addWidget(self.file,1);row.addWidget(browse);file_form.addRow('Archivo',row)
        self.sheet=QComboBox();self.column=QComboBox();file_form.addRow('Hoja',self.sheet);file_form.addRow('Columna de NPN',self.column);form.addRow(self.file_page)
        self.db_page=QWidget();db_form=QFormLayout(self.db_page);db_form.setContentsMargins(0,0,0,0)
        self.connection=QComboBox();refresh=QPushButton('Actualizar conexiones');refresh.clicked.connect(self.refresh_connections)
        row=QHBoxLayout();row.addWidget(self.connection,1);row.addWidget(refresh)
        self.connection_controls=QWidget(self.db_page);self.connection_controls.setLayout(row);self.connection_controls.hide()
        hint=QLabel('Precargados: sentencias.r1_r2. Public: base de la fuente seleccionada en la ventana principal. En este plugin se utiliza únicamente el R1.');hint.setWordWrap(True);db_form.addRow(hint)
        self.schema_label=QLabel('r1_r2');self.tables=QComboBox();list_button=QPushButton('Consultar tablas R1');list_button.clicked.connect(self.read_tables)
        row=QHBoxLayout();row.addWidget(self.tables,1);row.addWidget(list_button);db_form.addRow('Esquema',self.schema_label);db_form.addRow('Tabla y columna NPN',row);form.addRow(self.db_page)
        self.read_button=QPushButton('Leer R1 y calcular máximos');self.read_button.clicked.connect(self.read_maxima);form.addRow(self.read_button);outer.addWidget(self.inputs)
        self.origin_label=QLabel('R1 pendiente de cargar.');self.origin_label.setWordWrap(True);outer.addWidget(self.origin_label)
        self.counts=QLabel();self.counts.setWordWrap(True);outer.addWidget(self.counts)
        self.filters=QWidget();row=QHBoxLayout(self.filters);row.setContentsMargins(0,0,0,0)
        self.municipality=QComboBox();self.zone=QComboBox();self.search=QLineEdit();self.search.setPlaceholderText('Buscar prefijo, manzana o número de referencia…')
        row.addWidget(QLabel('Municipio'));row.addWidget(self.municipality,2);row.addWidget(QLabel('Zona–sector (6–9)'));row.addWidget(self.zone,1);row.addWidget(self.search,2);outer.addWidget(self.filters)
        self.tabs=QTabWidget();self.views={};self.fields={'Por zona-sector':ZONE_FIELDS,'Por prefijo 13':PREFIX_FIELDS,'Por manzana':BLOCK_FIELDS}
        for name,fields in self.fields.items():
            tree=QTreeWidget();tree.setRootIsDecorated(False);tree.setAlternatingRowColors(True);tree.setHeaderLabels(['Departamento','Municipio']+[label for label,_ in fields]);self.tabs.addTab(tree,name);self.views[name]=tree
        self.invalid=QTreeWidget();self.invalid.setRootIsDecorated(False);self.invalid.setHeaderLabels(['Fila de origen','NPN no utilizado','Motivo']);self.tabs.addTab(self.invalid,'Registros no utilizados');outer.addWidget(self.tabs,1)
        foot=QLabel('Las condiciones 8 y 9 no se validan en esta fase. Se muestran los máximos de todos los NPN válidos del R1 seleccionado, sin aprobar renumeraciones.');foot.setWordWrap(True);outer.addWidget(foot)
        self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.hide();outer.addWidget(self.progress)
        self.status=QLabel('Seleccione el R1 que servirá como referencia.');self.status.setWordWrap(True);outer.addWidget(self.status)
        actions=QHBoxLayout();self.export_button=QPushButton('Exportar máximos visibles a Excel');self.export_button.setEnabled(False);self.export_button.clicked.connect(self.export)
        close=QPushButton('Cerrar');close.clicked.connect(self.reject);actions.addWidget(self.export_button);candidates=QPushButton('Predios a renumerar · CICA / Modelo Interno');candidates.clicked.connect(self.open_candidates);actions.addWidget(candidates);actions.addStretch();actions.addWidget(close);outer.addLayout(actions)
        self.source_mode.currentIndexChanged.connect(self.change_source)
        self.connection.currentTextChanged.connect(self.connection_changed)
        self.tables.currentIndexChanged.connect(self.table_changed)
        self.sheet.currentTextChanged.connect(self.update_columns);self.column.currentIndexChanged.connect(self.invalidate)
        self.municipality.currentIndexChanged.connect(self.update_zones);self.zone.currentIndexChanged.connect(self.render);self.search.textChanged.connect(self.render)
        self.refresh_connections();self.change_source()

    def open_candidates(self):
        from .candidate_dialog import CandidateDialog
        CandidateDialog(self).exec_()

    def invalidate(self,*_):
        self.result=None;self.export_button.setEnabled(False)
        for name,tree in self.views.items():
            tree.clear();self.tabs.setTabText(self.tabs.indexOf(tree),name)
        self.search.clear()
        self.invalid.clear();self.origin_label.setText('R1 pendiente de cargar.');self.counts.clear()
        self.municipality.blockSignals(True);self.municipality.clear();self.municipality.addItem('Todos los municipios','');self.municipality.blockSignals(False)
        self.zone.blockSignals(True);self.zone.clear();self.zone.addItem('Todos los códigos zona–sector','');self.zone.blockSignals(False)

    def change_source(self,*_):
        mode=self.source_mode.currentIndex();self.file_page.setVisible(mode==0);self.db_page.setVisible(mode!=0)
        self.schema_label.setText('r1_r2' if mode==1 else 'public');self.tables.clear();self.invalidate();self.update_reference_date()
        if mode==1 and getattr(self,'source_municipality',''):self.read_tables()

    def set_source_municipality(self,code):
        code=code or ''
        if getattr(self,'source_municipality','')==code:return
        self.source_municipality=code
        if self.source_mode.currentIndex()==1:
            self.tables.clear();self.invalidate()
            if code:self.read_tables()

    def table_changed(self,*_):
        self.invalidate();self.update_reference_date()

    def update_reference_date(self):
        selection=self.tables.currentData() if self.source_mode.currentIndex()==1 else None
        match=re.fullmatch(r'r1_(\d{5})_(\d{8})',selection[0]) if selection else None
        date=datetime.strptime(match[2],'%Y%m%d').strftime('%d/%m/%Y') if match else 'Sin fecha seleccionada'
        self.source_mode.setItemText(1,'Opción 2: Archivos r1 y r2 precargados - '+date)

    def refresh_connections(self):
        settings=QgsSettings();settings.beginGroup('PostgreSQL/connections');names=sorted(settings.childGroups());settings.endGroup()
        previous=self.connection.currentText();self.connection.clear();self.connection.addItems(names)
        if previous in names:self.connection.setCurrentText(previous)

    def connection_changed(self,*_):self.tables.clear();self.invalidate()

    def params(self,preloaded=None,connection_name=None):
        name=self.connection.currentText() if connection_name is None else connection_name
        if not name:raise ValueError('Seleccione una conexión PostgreSQL guardada en QGIS.')
        settings=QgsSettings();group='PostgreSQL/connections/'+name
        params={key:settings.value(group+'/'+setting,'') for key,setting in [('host','host'),('port','port'),('dbname','database'),('user','username'),('password','password'),('service','service')]}
        params={key:str(value) for key,value in params.items() if value not in ('',None)}
        auth=settings.value(group+'/authcfg','')
        if auth:
            config=QgsAuthMethodConfig()
            if not QgsApplication.authManager().loadAuthenticationConfig(auth,config,True):raise ValueError('No se pudo leer la autenticación QGIS. Desbloquee el administrador de autenticación.')
            for key,field in [('user','username'),('password','password')]:
                if config.config(field):params[key]=config.config(field)
        if not params.get('password') and not params.get('service'):
            if name not in self._passwords:
                password,accepted=QInputDialog.getText(self,'Acceso a R1','Contraseña de la conexión (solo esta sesión):',QLineEdit.Password)
                if not accepted:raise ValueError('Consulta cancelada: no se suministró la contraseña.')
                self._passwords[name]=password
            params['password']=self._passwords[name]
        if (self.source_mode.currentIndex()==1 if preloaded is None else preloaded):
            params['dbname']='sentencias'
        return params

    def reference_params(self):
        if self.source_mode.currentIndex()==1:
            from .repository import repository_params
            return repository_params()
        params=getattr(self,'selected_source_params',None)
        if not params:raise ValueError('Seleccione la fuente de datos en la ventana principal antes de consultar Public.')
        return dict(params)

    def task(self,function):
        self.busy=True;self.inputs.setEnabled(False);self.filters.setEnabled(False);self.export_button.setEnabled(False);self.progress.show()
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future=executor.submit(function);loop=QEventLoop();timer=QTimer();timer.setInterval(50)
                timer.timeout.connect(lambda:loop.quit() if future.done() else None);timer.start()
                if not future.done():loop.exec_()
                timer.stop();return future.result()
        finally:
            self.busy=False;self.inputs.setEnabled(True);self.filters.setEnabled(True);self.progress.hide();self.export_button.setEnabled(self.result is not None)

    def choose_file(self):
        filename,_=QFileDialog.getOpenFileName(self,'Seleccionar R1','','R1 (*.xlsx *.txt *.TXT)')
        if not filename:return
        self.file.setText(filename);self.invalidate()
        self.sheet.blockSignals(True);self.sheet.clear();self.sheet.blockSignals(False)
        self.column.blockSignals(True);self.column.clear();self.column.blockSignals(False)
        if Path(filename).suffix.lower()=='.xlsx':
            try:
                names,selected,*_=inspect_excel(filename)
                self.sheet.blockSignals(True);self.sheet.clear();self.sheet.addItems(names);self.sheet.setCurrentText(selected);self.sheet.blockSignals(False)
                self.sheet.setEnabled(True);self.column.setEnabled(True);self.update_columns()
            except Exception as error:QMessageBox.warning(self,'No se leyó el Excel',str(error))
        else:
            self.sheet.clear();self.column.clear();self.column.addItem('TXT R1: posiciones 1–30',0);self.sheet.setEnabled(False);self.column.setEnabled(False)

    def update_columns(self,*_):
        self.invalidate()
        if not self.file.text() or Path(self.file.text()).suffix.lower()!='.xlsx' or not self.sheet.currentText():return
        try:
            _,_,self.header_row,headers,index=inspect_excel(self.file.text(),self.sheet.currentText())
            self.column.blockSignals(True);self.column.clear()
            for number,header in enumerate(headers):self.column.addItem(f'{number+1}: {header or "Sin encabezado"}',number)
            self.column.setCurrentIndex(index);self.column.blockSignals(False)
        except Exception as error:
            self.column.blockSignals(False);self.column.clear();QMessageBox.warning(self,'Columna NPN no disponible',str(error))

    def read_tables(self):
        try:
            params=self.reference_params();schema=self.schema_label.text();preloaded=self.source_mode.currentIndex()==1
            self.status.setText('Consultando tablas con columna de número predial…')
            tables=self.task(lambda:list_tables(params,schema,preloaded))
            self.tables.clear()
            if preloaded:
                latest={}
                for table,column in tables:
                    code,stamp=table.split('_')[1:]
                    try:datetime.strptime(stamp,'%Y%m%d')
                    except ValueError:continue
                    if code not in latest or stamp>latest[code][0]:latest[code]=(stamp,table,column)
                for code,(stamp,table,column) in sorted(latest.items()):
                    department,municipality=self.catalog.get(code,('Sin departamento identificado','Municipio no registrado'))
                    date=datetime.strptime(stamp,'%Y%m%d').strftime('%d/%m/%Y')
                    self.tables.addItem(f'{code} · {municipality} · {department} · {date}',(table,column))
            else:
                for table,column in tables:self.tables.addItem(table+' · '+column,(table,column))
            code=getattr(self,'source_municipality','') if preloaded else ''
            if code:
                match=next((index for index in range(self.tables.count()) if self.tables.itemData(index)[0].split('_')[1]==code),-1)
                self.tables.setCurrentIndex(match)
                if match<0:
                    self.update_reference_date();self.status.setText(f'No hay R1 precargado disponible para el municipio seleccionado: {code}.');return
            self.update_reference_date()
            self.status.setText(f'{len(tables)} tablas disponibles en {params.get("dbname",params.get("service",""))}.{schema}. Seleccione el R1 y pulse Leer.')
        except Exception as error:QMessageBox.warning(self,'No se consultaron las tablas',str(error))

    def read_maxima(self):
        self.invalidate()
        try:
            if self.source_mode.currentIndex()==0:
                filename=self.file.text()
                if not filename:raise ValueError('Seleccione el archivo R1.')
                if Path(filename).suffix.lower()=='.xlsx' and self.column.currentData() is None:raise ValueError('Seleccione la hoja y columna NPN.')
                sheet=self.sheet.currentText();header=self.header_row;column=self.column.currentData() or 0
                origin=Path(filename).name+(f' · hoja {sheet} · columna {column+1}' if sheet else '')
                function=lambda:build_maxima(file_records(filename,sheet,header,column))
            else:
                if not self.tables.currentData():raise ValueError('Consulte y seleccione una tabla R1.')
                params=self.reference_params();schema=self.schema_label.text();table,column=self.tables.currentData()
                origin=f'{params.get("dbname",params.get("service",""))}.{schema}.{table} · {column}'
                function=lambda:build_maxima(database_records(params,schema,table,column))
            self.status.setText('Leyendo R1 y calculando máximos…')
            result=self.task(function);self.set_result(result,origin)
            self.status.setText('Consulta terminada.' if result.unique_npns else 'No se encontraron NPN válidos. Revise la hoja, columna y registros no utilizados.')
        except Exception as error:
            self.status.setText('No se completó la consulta.');QMessageBox.warning(self,'No se pudo leer el R1',str(error))

    def set_result(self,result,origin):
        self.result=result;self.origin=origin;self.origin_label.setText('R1 de referencia: '+origin)
        self.counts.setText(f'Leídos: {result.source_rows:,} · NPN únicos válidos: {result.unique_npns:,} · Duplicados excluidos: {result.duplicates:,} · Vacíos: {result.blanks:,} · Inválidos: {len(result.invalid):,}'.replace(',','.'))
        self.municipality.blockSignals(True);self.municipality.clear();self.municipality.addItem('Todos los municipios','')
        codes=sorted({row['municipality'] for row in result.zones},key=lambda code:(*self.catalog.get(code,('','')),code))
        for code in codes:
            department,name=self.catalog.get(code,('Sin departamento identificado','Sin municipio identificado'))
            self.municipality.addItem(f'{department} · {name} ({code})',code)
        self.municipality.blockSignals(False);self.update_zones()
        self.invalid.clear()
        for row in result.invalid:self.invalid.addTopLevelItem(QTreeWidgetItem([str(value) for value in row]))
        self.export_button.setEnabled(True)

    def update_zones(self,*_):
        previous=self.zone.currentData();municipality=self.municipality.currentData() or ''
        codes=sorted({row['zone_sector'] for row in self.result.zones if not municipality or row['municipality']==municipality}) if self.result else []
        self.zone.blockSignals(True);self.zone.clear();self.zone.addItem('Todos los códigos zona–sector','')
        for code in codes:self.zone.addItem(zone_name(code[:2])+' · '+code,code)
        index=self.zone.findData(previous);self.zone.setCurrentIndex(max(0,index));self.zone.blockSignals(False);self.render()

    def render(self,*_):
        if self.result is None:return
        datasets={'Por zona-sector':self.result.zones,'Por prefijo 13':self.result.prefixes,'Por manzana':self.result.blocks}
        for name,tree in self.views.items():
            rows=visible_rows(datasets[name],self.municipality.currentData() or '',self.zone.currentData() or '',self.search.text(),self.catalog)
            tree.clear()
            for row in rows:
                values=list(self.catalog.get(row['municipality'],('No identificado','No identificado')))+[row[key] for _,key in self.fields[name]]
                item=QTreeWidgetItem([str(value) for value in values])
                for index,value in enumerate(values):
                    if isinstance(value,int):item.setTextAlignment(index,Qt.AlignRight|Qt.AlignVCenter)
                tree.addTopLevelItem(item)
            self.tabs.setTabText(self.tabs.indexOf(tree),f'{name} ({len(rows)})')
            for column in range(tree.columnCount()):tree.resizeColumnToContents(column)

    def export(self):
        if self.result is None:return
        filename,_=QFileDialog.getSaveFileName(self,'Guardar máximos R1','maximos_R1.xlsx','Excel (*.xlsx)')
        if not filename:return
        if not filename.lower().endswith('.xlsx'):filename+='.xlsx'
        result=self.result;origin=self.origin;municipality=self.municipality.currentData() or '';zone=self.zone.currentData() or '';search=self.search.text()
        try:
            self.task(lambda:export_maxima(filename,result,origin,self.catalog,municipality,zone,search));self.status.setText('Reporte guardado: '+filename)
        except Exception as error:QMessageBox.warning(self,'No se exportó el reporte',str(error))

    def closeEvent(self,event):
        if self.busy:self.status.setText('Espere a que termine la lectura o exportación.');event.ignore()
        else:event.accept()
    def reject(self):
        if not self.busy:super().reject()
