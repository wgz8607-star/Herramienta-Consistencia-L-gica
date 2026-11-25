from .build_info import TITLE
from .logic_dialog import show_renumbering_logic
from .provisional_style import ProvisionalLabel,emphasize_item,emphasize_workbook
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QComboBox,QLineEdit,QPushButton,QLabel,QTreeWidget,QTreeWidgetItem,QMessageBox,QFileDialog,QCheckBox,QWidget,QHBoxLayout,QGroupBox,QSplitter
from openpyxl import Workbook
from .schema_selector import SchemaSelector
from .database import model_schemas,model_municipalities,source_records,cica_municipalities,cica_copy_date
from .candidates import identify_candidates,candidate_statistics,new_block_statistics,new_block_groups,block_name

HEADERS=['Prefijo territorial','Agrupación','Predios a renumerar','Manzanas–veredas','Terrenos distintos (1–21)','Predios condición 8/9']


class CandidateDialog(QDialog):
    def __init__(self,parent,window_parent=None):
        super().__init__(parent if window_parent is None else window_parent);self.owner=parent;self.result=None;self.origin='';self.cica_codes=[];self.copy_date='Fecha de copia pendiente de consultar';self._copy_consulted=False
        self.setWindowTitle(TITLE+' · Seleccionar fuente de datos');self.resize(1400,950)
        self.setWindowFlags(self.windowFlags()|Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint)
        self.setStyleSheet('QDialog { background: #F3F6FA; } QLabel { color: #17324D; } QComboBox QAbstractItemView { background: #FFFFFF; color: #17324D; selection-background-color: #0066B3; selection-color: #FFFFFF; font-weight: normal; } QComboBox QAbstractItemView::item { min-height: 26px; padding: 4px; } QComboBox QAbstractItemView::item:selected { background: #0066B3; color: #FFFFFF; } QComboBox,QLineEdit { background: #FFFFFF; border: 1px solid #CDDFEF; border-radius: 4px; padding: 6px; } QPushButton { background: #0066B3; color: white; border-radius: 5px; padding: 8px 12px; } QPushButton:disabled { background: #E9ECEF; color: #7B8490; } QTreeWidget { background: white; alternate-background-color: #F3F8FC; border: 1px solid #D9E5EF; } QHeaderView::section { background: #0066B3; color: white; padding: 7px; }')
        layout=QVBoxLayout(self)
        self.build_title=title=QLabel(TITLE);title.setStyleSheet('font-size: 20px; font-weight: bold; color: #0066B3;');layout.addWidget(title)
        source_card=QGroupBox('1. Fuente y referencia');source_card.setStyleSheet('QGroupBox { background: white; border: 1px solid #D9E5EF; border-radius: 8px; margin-top: 12px; padding: 14px; font-weight: bold; color: #0066B3; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }');form=QFormLayout(source_card);form.setSpacing(8);layout.addWidget(source_card)
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
            form.addRow(label,field);field.textChanged.connect(self.model_connection_edited)
        self.connection_mode.currentIndexChanged.connect(self.connection_mode_changed)
        self.schema=SchemaSelector();self.schema.catalog=parent.catalog;self.list_button=QPushButton('Consultar esquemas');form.addRow(self.list_button);form.addRow('Esquema por municipio · DIVIPOLA',self.schema)
        self.model_municipality=QComboBox();form.addRow('Municipio a validar',self.model_municipality)
        self.model_location=QLabel('Seleccione un esquema para consultar su municipio.');self.model_location.setWordWrap(True);form.addRow(self.model_location)
        self.model_municipality.currentIndexChanged.connect(self.model_municipality_changed)
        self.cica_lookup=QPushButton('Consultar departamentos y municipios CICA');form.addRow(self.cica_lookup)
        self.department=QComboBox();self.cica_municipality=QComboBox();form.addRow('Departamento',self.department);form.addRow('Municipio CICA',self.cica_municipality)
        self.copy_label=QLabel(self.copy_date);form.insertRow(form.getWidgetPosition(self.cica_lookup)[0]+1,'',self.copy_label)
        self.copy_label.setStyleSheet('background: #E8F1FA; color: #0066B3; font-weight: bold; padding: 8px; border-left: 4px solid #0066B3;')
        self.cica_lookup.clicked.connect(self.load_cica_municipalities);self.department.currentIndexChanged.connect(self.update_cica_municipalities);self.cica_municipality.currentIndexChanged.connect(self.update_available_zones)
        self.note=note=ProvisionalLabel('CICA: 7, 8 o 9 en posición 14 o 18. Modelo Interno: letra en posición 14 o 18. CICA: solo etapa VALIDADO y estado_control DESCARGADO_AL_SNC. Modelo Interno: sin filtro de etapa o estado. Las condiciones 8 y 9 (posición 22) quedan identificadas para revisión especial.');note.setWordWrap(True);layout.addWidget(note)
        self.stats_button=QPushButton('Ver estadísticas CICA…');self.stats_button.clicked.connect(self.open_statistics);layout.addWidget(self.stats_button)
        self.read=QPushButton('Identificar predios a renumerar');layout.addWidget(self.read)
        self.status=ProvisionalLabel('Seleccione la fuente y su conexión.');self.status.setWordWrap(True);layout.addWidget(self.status)
        results_title=QLabel('2. Alcance y diagnóstico · Manzanas - Veredas nuevas y predios a renumerar');results_title.setStyleSheet('color: #0066B3; font-size: 16px; font-weight: bold;');layout.addWidget(results_title)
        self.scope_widget=QWidget();self.scope_layout=QHBoxLayout(self.scope_widget);self.scope_layout.setContentsMargins(0,0,0,0);self.scope_boxes={};self.scope_layout.addWidget(ProvisionalLabel('Identifique los provisionales para seleccionar las zonas.'));layout.addWidget(self.scope_widget)
        self.scope_status=ProvisionalLabel('Alcance pendiente.');self.scope_status.setWordWrap(True);layout.addWidget(self.scope_status)
        split=QSplitter(Qt.Vertical);layout.addWidget(split,1)
        top=QWidget();top_layout=QVBoxLayout(top);top_layout.setContentsMargins(0,0,0,0);top_layout.addWidget(ProvisionalLabel('Manzanas o veredas nuevas · provisional en posición 14'))
        self.new_blocks=QTreeWidget();self.new_blocks.setRootIsDecorated(True);self.new_blocks.setAlternatingRowColors(True);self.new_blocks.setHeaderLabels(HEADERS);top_layout.addWidget(self.new_blocks)
        group_controls=QHBoxLayout();self.expand_blocks=QPushButton('Desagrupar detalle');self.collapse_blocks=QPushButton('Agrupar por zona–sector');self.expand_blocks.clicked.connect(self.new_blocks.expandAll);self.collapse_blocks.clicked.connect(self.new_blocks.collapseAll);group_controls.addWidget(self.expand_blocks);group_controls.addWidget(self.collapse_blocks);group_controls.addStretch();top_layout.addLayout(group_controls);split.addWidget(top)
        bottom=QWidget();bottom_layout=QVBoxLayout(bottom);bottom_layout.setContentsMargins(0,0,0,0);bottom_layout.addWidget(QLabel('Predios a renumerar · zona–sector y manzana o vereda'))
        self.tree=QTreeWidget();self.tree.setAlternatingRowColors(True);self.tree.setRootIsDecorated(True);self.tree.setHeaderLabels(HEADERS);bottom_layout.addWidget(self.tree);split.addWidget(bottom);split.setSizes([220,300])
        self.propose_button=QPushButton('3. Generar propuesta y comparar archivo…');self.propose_button.setEnabled(False);self.propose_button.clicked.connect(self.open_proposal);layout.addWidget(self.propose_button)
        self.export=QPushButton('Exportar identificación a Excel');self.export.setEnabled(False)
        export_actions=QHBoxLayout();export_actions.addWidget(self.export);self.logic_button=QPushButton('Ver lógica de renumeración');self.logic_button.clicked.connect(lambda:show_renumbering_logic(self));export_actions.addWidget(self.logic_button);layout.addLayout(export_actions)
        self.r1_status=QLabel('Seleccione departamento y municipio para leer el R1 precargado.');self.r1_status.setWordWrap(True)
        self.r1_button=QPushButton('Leer R1 del municipio');self.r1_button.clicked.connect(self.read_selected_r1)
        self.maxima_button=QPushButton('Consultar máximos del R1');self.maxima_button.clicked.connect(self.open_r1);self.maxima_button.setEnabled(False)
        r1_row=QHBoxLayout();r1_row.addWidget(self.r1_status,1);r1_row.addWidget(self.r1_button);r1_row.addWidget(self.maxima_button)
        form.insertRow(form.getWidgetPosition(self.cica_municipality)[0]+1,'R1 precargado',r1_row)
        self._r1_code=''
        self.cica_municipality.currentIndexChanged.connect(self.update_r1_availability);self.model.currentIndexChanged.connect(self.update_r1_availability);self.schema.currentTextChanged.connect(self.model_schema_selected)
        self.model.currentIndexChanged.connect(self.change_source);self.connection.currentTextChanged.connect(self.change_source)
        self.schema.currentTextChanged.connect(self.invalidate)
        self.list_button.clicked.connect(self.list_schemas);self.read.clicked.connect(self.load);self.export.clicked.connect(self.save)
        self.change_source();self.connection_mode_changed();self.update_available_zones();self.update_r1_availability()

    def reference_municipality(self):
        if self.model.currentText()=='CICA':return self.cica_municipality.currentData() or ''
        return self.model_municipality.currentData() or ''

    def model_connection_edited(self,*_):
        self.invalidate()
        if self.model.currentText()!='CICA':self.schema.clear()

    def model_municipality_changed(self,*_):
        code=self.model_municipality.currentData()
        if code:
            department,name=self.owner.catalog.get(code,('Departamento no identificado','Municipio no identificado'))
            self.model_location.setText(f'Municipio a validar: {name} · {code} · {department}')
        else:self.model_location.setText('Seleccione el municipio del esquema para validar su renumeración.')
        self.invalidate();self.update_r1_availability()

    def model_schema_selected(self,*_):
        if self.model.currentText()=='CICA':return
        self.model_municipality.clear();self.invalidate();self.update_r1_availability()
        schema=self.schema.currentText()
        if not schema:
            self.model_location.setText('Seleccione un esquema para consultar su municipio.');return
        self.model_location.setText('Consultando municipio del esquema…')
        try:
            params=self.params();codes=self.run(lambda:model_municipalities(params,schema))
            self.model_municipality.blockSignals(True)
            if len(codes)!=1:self.model_municipality.addItem('Seleccione municipio…',None)
            for code in codes:
                department,name=self.owner.catalog.get(code,('Departamento no identificado','Municipio no identificado'))
                self.model_municipality.addItem(f'{name} · {code} · {department}',code)
            self.model_municipality.blockSignals(False);self.model_municipality_changed()
            if len(codes)==1:
                department,name=self.owner.catalog.get(codes[0],('Departamento no identificado','Municipio no identificado'))
                self.schema.locations[schema]=(department,name,codes[0])
            if not codes:self.model_location.setText('No se identificó municipio: revise los NPN del esquema seleccionado.')
        except Exception as error:
            self.model_location.setText('No se pudo determinar el municipio del esquema.')
            QMessageBox.warning(self,'Municipio del Modelo Interno',str(error))

    def update_r1_availability(self,*_):
        code=self.reference_municipality()
        self.r1_button.setEnabled(bool(code))
        if self._r1_code!=code:
            self._r1_code='';self.maxima_button.setEnabled(False);self.owner.invalidate()
            self.r1_status.setText('R1 precargado pendiente de leer · '+code if code else 'Seleccione departamento y municipio para leer el R1 precargado.')
        self.update_proposal_availability()

    def read_selected_r1(self):
        from datetime import datetime
        from .repository import repository_params
        from .database import list_tables,database_records
        from .core import build_maxima
        code=self.reference_municipality()
        if not code:return
        self.maxima_button.setEnabled(False);self.owner.invalidate();self._r1_code=''
        try:
            params=repository_params();self.r1_status.setText('Leyendo R1 del municipio '+code+'…')
            def read():
                tables=list_tables(params,'r1_r2',True);matches=[]
                for table,column in tables:
                    _,municipality,stamp=table.split('_')
                    if municipality!=code:continue
                    try:date=datetime.strptime(stamp,'%Y%m%d')
                    except ValueError:continue
                    matches.append((date,table,column))
                if not matches:raise ValueError('No hay R1 precargado disponible para '+code+'.')
                date,table,column=max(matches)
                result=build_maxima(database_records(params,'r1_r2',table,column))
                return result,table,date
            result,table,date=self.run(read)
            self.owner.source_municipality=code
            self.owner.set_result(result,'sentencias.r1_r2.'+table)
            self._r1_code=code;self.maxima_button.setEnabled(True)
            self.r1_status.setText(f'Leído · {code} · Vigencia: {date:%d/%m/%Y} · {result.unique_npns:,} NPN únicos'.replace(',','.'))
        except Exception as error:
            self.r1_status.setText('R1 no disponible · '+code);QMessageBox.warning(self,'No se leyó el R1',str(error))
        self.update_proposal_availability()

    def open_r1(self):
        if not self._r1_code or self.owner.result is None:return
        self.owner.inputs.hide()
        self.owner.showNormal();self.owner.raise_();self.owner.activateWindow()

    def invalidate(self,*_):
        self.result=None;self.tree.clear();self.new_blocks.clear();self.export.setEnabled(False);self.status.setText('Fuente pendiente de consultar.')
        self.propose_button.setEnabled(False);self.scope_status.setText('Alcance pendiente.')
        for checkbox in self.scope_boxes.values():checkbox.setEnabled(False)

    def change_source(self,*_):
        self.schema.clear();self.schema.locations={};cica=self.model.currentText()=='CICA'
        for field in [self.connection_mode,self.connection,self.model_municipality]:
            field.setVisible(not cica);self.connection_form.labelForField(field).setVisible(not cica)
        for field in self.direct.values():
            visible=not cica and self.connection_mode.currentIndex()==1
            field.setVisible(visible);self.connection_form.labelForField(field).setVisible(visible)
        for field in [self.department,self.cica_municipality]:
            field.setVisible(cica);self.connection_form.labelForField(field).setVisible(cica)
        self.cica_lookup.setVisible(cica);self.list_button.setVisible(not cica);self.model_location.setVisible(not cica)
        self.schema.setVisible(not cica);self.connection_form.labelForField(self.schema).setVisible(not cica)
        self.copy_label.setVisible(cica and self._copy_consulted)
        self.stats_button.setVisible(cica)
        self.note.setText(('CICA: provisionales 7, 8 o 9 en posición 14 o 18. Solo VALIDADO / DESCARGADO_AL_SNC.' if cica else 'Modelo Interno: letra en posición 14 o 18.')+' PH y condominios comparten terreno por prefijo 1–22; condición 2 comparte con su predio base; se admiten uno o varios predios de condición 5 CANCELADO con el predio base válido, con o sin compañero de condición 2.')
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
        self._copy_consulted=True
        self.copy_label.setVisible(self.model.currentText()=='CICA')
        try:
            value=self.run(lambda:cica_copy_date(params))
            self.copy_date=value.strftime('%d/%m/%Y %H:%M:%S') if value else 'Fecha no disponible'
            self.copy_label.setText(('Copia base CICA · Leído — Fecha y hora del corte: ' if value else 'Copia base CICA — ')+self.copy_date);self.copy_label.setToolTip('Último registro de public.copia_cica_progreso · inicio')
        except Exception as error:
            self.copy_date='Fecha no disponible';self.copy_label.setText('Copia base CICA — Fecha y hora del corte: '+self.copy_date);self.copy_label.setToolTip(str(error))

    def update_available_zones(self,*_):
        self.invalidate()
        self.stats_button.setEnabled(bool(self.cica_municipality.currentData()))

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
        self._copy_consulted=False;self.copy_date='Fecha de copia pendiente de consultar';self.copy_label.hide()
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
        self.schema.blockSignals(True);self.schema.clear();self.schema.locations={};self.schema.blockSignals(False);self.model_municipality.clear();self.update_r1_availability()
        try:
            params=self.params();self.invalidate();self.status.setText('Consultando esquemas…')
            schemas=self.run(lambda:model_schemas(params));self.schema.blockSignals(True);self.schema.clear();self.schema.addItems(schemas);self.schema.setCurrentIndex(-1);self.schema.blockSignals(False);self.model_municipality.clear();self.model_location.setText('Seleccione un esquema para consultar su municipio.');self.update_r1_availability()
            self.status.setText(f'{len(schemas)} esquemas con ILC_Predio disponibles.')
        except Exception as error:QMessageBox.warning(self,'No se consultaron los esquemas',str(error))

    def load(self):
        self.invalidate()
        try:
            cica=self.model.currentText()=='CICA'
            code=self.reference_municipality()
            if not code:raise ValueError('Consulte y seleccione el municipio de la fuente antes de identificar los provisionales.')
            if code and (len(code)!=5 or not code.isascii() or not code.isdigit()):raise ValueError('Ingrese una DIVIPOLA de cinco dígitos.')
            model='CICA' if self.model.currentText()=='CICA' else 'Modelo Interno';schema=self.schema.currentText()
            if not schema:raise ValueError('Consulte y seleccione el esquema del Modelo Interno.')
            zones=None  # All zones of the selected municipality.
            params=self.params();self.status.setText('Leyendo los predios de la fuente…')
            result=self.run(lambda:identify_candidates(source_records(params,model,schema,code,zones),model))
            self.result=result;self.origin=f'{model} · {params.get("dbname",params.get("service",""))}.{schema} · DIVIPOLA: {code or "Todos"}'
            if model=='CICA':self.origin+=' · Corte: '+self.copy_date+' · etapa=VALIDADO · estado_control=DESCARGADO_AL_SNC · Zonas: todas'
            self.build_scope()
            self.render_candidate_statistics()
            pending=sum(row[8] in '89' for row in result['rows'])
            self.status.setText(f'Fuente: Leído · {self.origin}\nLeídos: {result["total"]} · NPN únicos válidos: {result["unique"]} · Provisionales: {len(result["rows"])} · Predios de condición 8/9: {pending} · Duplicados excluidos: {result["duplicates"]} · Inválidos: {len(result["invalid"])}')
            self.export.setEnabled(True)
        except Exception as error:QMessageBox.warning(self,'No se identificaron los predios',str(error))

    def render_candidate_statistics(self):
        self.tree.clear();self.new_blocks.clear()
        if self.result is None:return
        rows=self.selected_candidate_rows()
        for sector in new_block_groups(rows):
            parent=QTreeWidgetItem(self.stat_values(sector,'Zona–sector (1–9)'))
            self.new_blocks.addTopLevelItem(parent)
            for block in sector['children']:
                parent.addChild(QTreeWidgetItem(self.stat_values(block,block_name(block['prefix'])+' nueva (1–17)')))
        for column in range(self.new_blocks.columnCount()):self.new_blocks.resizeColumnToContents(column)
        for sector in candidate_statistics(rows):
            parent=QTreeWidgetItem(self.stat_values(sector,'Zona–sector (1–9)'))
            self.tree.addTopLevelItem(parent)
            for block in sector['children']:
                parent.addChild(QTreeWidgetItem(self.stat_values(block,block_name(block['prefix'])+' (1–17)')))
        for column in range(self.tree.columnCount()):self.tree.resizeColumnToContents(column)
        for tree in (self.new_blocks,self.tree):
            for index in range(tree.topLevelItemCount()):
                root=tree.topLevelItem(index);emphasize_item(root,2)
                for child_index in range(root.childCount()):
                    child=root.child(child_index);emphasize_item(child,2)
                    prefix=child.text(0)
                    if len(prefix)==17 and (prefix[13] in '789' if self.model.currentText()=='CICA' else prefix[13].isalpha()):emphasize_item(child,0)
        self.update_proposal_availability()

    def build_scope(self):
        while self.scope_layout.count():
            item=self.scope_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        self.scope_boxes={}
        from .core import zone_name
        for code in sorted({row[0][5:7] for row in self.result['rows']}):
            checkbox=QCheckBox(zone_name(code)+' · '+code);checkbox.setChecked(True)
            checkbox.toggled.connect(self.render_candidate_statistics);self.scope_layout.addWidget(checkbox);self.scope_boxes[code]=checkbox
        self.scope_layout.addStretch()

    def selected_candidate_rows(self):
        if self.result is None:return []
        if not self.scope_boxes:return self.result['rows']
        codes={code for code,box in self.scope_boxes.items() if box.isChecked()}
        return [row for row in self.result['rows'] if row[0][5:7] in codes]

    def update_proposal_availability(self):
        rows=self.selected_candidate_rows()
        if self.result is not None:
            new_blocks=len({row[0][:17] for row in rows if row[7] in ('Manzana','Manzana y terreno')})
            active=sum(len(row)>10 and row[10]=='ACTIVO' for row in rows);cancelled=sum(len(row)>10 and row[10]=='CANCELADO' for row in rows)
            self.scope_status.setText(f'Provisionales: {len(rows)} · {len({row[0][:21] for row in rows})} terrenos distintos · {new_blocks} manzanas/veredas nuevas · Activos: {active} · Cancelados: {cancelled} · Otros/sin información: {len(rows)-active-cancelled}. Un grupo de terreno consume un consecutivo.')
        same=bool(rows) and bool(self._r1_code) and {row[0][:5] for row in rows}=={self._r1_code}
        self.propose_button.setEnabled(same and self.owner.result is not None)
        if rows and not same:self.propose_button.setToolTip('Lea el R1 del mismo municipio de los provisionales seleccionados.')
        else:self.propose_button.setToolTip('Generar una propuesta de consulta; no modifica la base.')

    def open_proposal(self):
        from .renumbering import generate_proposal
        from .proposal_dialog import ProposalDialog
        rows=list(self.selected_candidate_rows());r1=self.owner.result
        if not rows or r1 is None or {row[0][:5] for row in rows}!={self._r1_code}:
            QMessageBox.warning(self,'Referencia pendiente','Lea el R1 del mismo municipio y seleccione al menos una zona.');return
        model='CICA' if self.model.currentText()=='CICA' else 'Modelo Interno'
        zones=sorted({row[0][5:7] for row in rows})
        try:
            proposal=self.run(lambda:generate_proposal(rows,r1,model))
            context=self.origin+'\nR1: '+self.owner.origin+' · SHA256: '+r1.fingerprint+f' · R1 inválidos excluidos: {len(r1.invalid)}'+'\nZonas seleccionadas: '+', '.join(zones)+f' · Registros inválidos excluidos de la fuente: {len(self.result["invalid"])}'
            dialog=ProposalDialog(proposal,context,self);dialog.showMaximized();dialog.exec_()
        except Exception as error:QMessageBox.warning(self,'No se generó la propuesta',str(error))

    @staticmethod
    def stat_values(item,level):
        return [item['prefix'],level]+[str(item[key]) for key in ('predios','blocks','plots','pending')]

    def save(self):
        if self.result is None:return
        filename,_=QFileDialog.getSaveFileName(self,'Guardar identificación','predios_a_renumerar.xlsx','Excel (*.xlsx)')
        if not filename:return
        if not filename.lower().endswith('.xlsx'):filename+='.xlsx'
        try:
            rows=self.selected_candidate_rows()
            book=Workbook();summary=book.active;summary.title='Resumen';summary.append(['Origen',self.origin]);summary.append(['Zonas seleccionadas',', '.join(sorted({row[0][5:7] for row in rows}))]);summary.append(['Alcance','Identificación de provisionales seleccionados; no modifica la base.'])
            for key in ('total','unique','duplicates'):summary.append([key,self.result[key]])
            new_groups=book.create_sheet('Nuevas por zona-sector');new_groups.append(HEADERS)
            for sector in new_block_groups(rows):new_groups.append(self.stat_values(sector,'Zona–sector (1–9)'))
            new_blocks=book.create_sheet('Manzanas-Veredas nuevas');new_blocks.append(HEADERS)
            for block in new_block_statistics(rows):new_blocks.append(self.stat_values(block,block_name(block['prefix'])+' nueva (1–17)'))
            sectors=book.create_sheet('Por zona-sector');sectors.append(HEADERS)
            blocks=book.create_sheet('Por manzana-vereda');blocks.append(HEADERS)
            for item in candidate_statistics(rows):
                sectors.append(self.stat_values(item,'Zona–sector (1–9)'))
                for block in item['children']:blocks.append(self.stat_values(block,block_name(block['prefix'])+' (1–17)'))
            invalid=book.create_sheet('No utilizados');invalid.append(['Fila de lectura','NPN','Motivo'])
            for row in self.result['invalid']:invalid.append(row)
            for sheet in book:
                sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
                for row in sheet:
                    for cell in row:
                        if isinstance(cell.value,str):cell.data_type='s'
            emphasize_workbook(book)
            book.save(filename);book.close();self.status.setText('Exportado: '+filename)
        except Exception as error:QMessageBox.warning(self,'No se exportó',str(error))

    def reject(self):
        if not self.owner.busy:super().reject()

    def closeEvent(self,event):
        if self.owner.busy:event.ignore()
        else:event.accept()
