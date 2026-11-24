"""Review and compare a proposal. This module never writes to a database."""
from collections import Counter
from pathlib import Path
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QTreeWidget,QTreeWidgetItem,QTabWidget,QComboBox,QLineEdit,QFileDialog,QMessageBox,QMenu,QWidgetAction)
from openpyxl import load_workbook,Workbook
from openpyxl.styles import Font,PatternFill
from .renumbering import read_comparison,compare_proposal

PROPOSAL_FIELDS=[('Provisional','old'),('Definitivo esperado','new'),('Resultado','status'),('Observación','reason'),('Máximo manzana/vereda R1','base_m'),('Inicio manzana/vereda','next_m'),('Máximo terreno R1','base_t'),('Inicio terreno','next_t')]
COMPARE_FIELDS=[('Provisional','old'),('Definitivo esperado','expected'),('Definitivo del archivo','actual'),('Resultado','status'),('Observación','reason'),('Máximo manzana/vereda R1','base_m'),('Inicio manzana/vereda','next_m'),('Máximo terreno R1','base_t'),('Inicio terreno','next_t'),('Fila Excel','line')]



class ProposalDialog(QDialog):
    def __init__(self,proposal,context,parent):
        super().__init__(parent);self.proposal=proposal;self.context=context;self.file_rows=[];self.invalid_rows=[];self.comparison=[];self.filename=''
        self.by_old={row['old']:row for row in proposal};self.column_filters={'Propuesta':{},'Comparación':{}}
        self.fields={'Propuesta':PROPOSAL_FIELDS,'Comparación':COMPARE_FIELDS}
        reference=getattr(getattr(parent,'owner',None),'result',None)
        self.prefix_max={row['prefix13']:int(row['max_m']) for row in reference.prefixes} if reference is not None else {}
        for row in proposal:
            if row['old'][:13] not in self.prefix_max and row.get('base_m') is not None:self.prefix_max[row['old'][:13]]=row['base_m']
        self.setWindowTitle('3. Propuesta de renumeración y comparación');self.resize(1450,900)
        self.setWindowFlags(self.windowFlags()|Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint)
        self.setStyleSheet(parent.styleSheet())
        layout=QVBoxLayout(self)
        title=QLabel('3. Propuesta y comparación');title.setStyleSheet('font-size: 22px; color: #0066B3; font-weight: bold;');layout.addWidget(title)
        origin=QLabel(context);origin.setWordWrap(True);layout.addWidget(origin)
        note=QLabel('Propuesta de consulta: no modifica la base. Consecutivos sin saltos, en orden de provisionales. Excel de comparación: A = nuevo; B = provisional. Los pendientes no se aprueban. «Coincide» compara archivo y propuesta; no acredita cambios aplicados en la base.');note.setWordWrap(True);layout.addWidget(note)
        totals=Counter(row['status'] for row in proposal)
        self.summary=QLabel(f'Provisionales en la propuesta: {len(proposal)} · Generados: {totals["Generado"]} · Pendientes: {totals["Pendiente"]}');self.summary.setWordWrap(True);layout.addWidget(self.summary)
        row=QHBoxLayout();self.browse=QPushButton('Cargar archivo de renumeración…');self.browse.clicked.connect(self.choose_file);row.addWidget(self.browse)
        self.sheet=QComboBox();row.addWidget(self.sheet,1);self.compare_button=QPushButton('Comparar columnas A / B');self.compare_button.setEnabled(False);self.compare_button.clicked.connect(self.compare);row.addWidget(self.compare_button);layout.addLayout(row)
        self.file_status=QLabel('Archivo pendiente de cargar. Solo se presentan los provisionales de la propuesta seleccionada.');self.file_status.setWordWrap(True);layout.addWidget(self.file_status)
        row=QHBoxLayout();self.status_filter=QComboBox();self.status_filter.addItem('Todos los resultados','');self.search=QLineEdit();self.search.setPlaceholderText('Buscar NPN o prefijo…');row.addWidget(self.status_filter);row.addWidget(self.search,1);layout.addLayout(row)
        controls=QHBoxLayout();expand=QPushButton('Desagrupar detalle');expand.clicked.connect(lambda:[tree.expandAll() for tree in self.views.values()]);collapse=QPushButton('Agrupar');collapse.clicked.connect(lambda:[tree.collapseAll() for tree in self.views.values()]);clear=QPushButton('Limpiar filtros de columnas');clear.clicked.connect(self.clear_column_filters);controls.addWidget(expand);controls.addWidget(collapse);controls.addWidget(clear);controls.addStretch();layout.addLayout(controls)
        self.tabs=QTabWidget();self.views={}
        for name,fields in [('Propuesta',PROPOSAL_FIELDS),('Comparación',COMPARE_FIELDS)]:
            tree=QTreeWidget();tree.setRootIsDecorated(True);tree.setAlternatingRowColors(True);tree.setHeaderLabels([label+' ▾' for label,_ in fields]);tree.header().setSectionsClickable(True);tree.header().sectionClicked.connect(lambda column,view=name:self.open_column_filter(view,column));self.tabs.addTab(tree,name);self.views[name]=tree
        self.invalid=QTreeWidget();self.invalid.setRootIsDecorated(False);self.invalid.setHeaderLabels(['Fila Excel','A · Nuevo','B · Provisional','Motivo']);self.tabs.addTab(self.invalid,'Filas no utilizadas');layout.addWidget(self.tabs,1)
        row=QHBoxLayout();export=QPushButton('Exportar propuesta y comparación');export.clicked.connect(self.export);row.addWidget(export);row.addStretch();close=QPushButton('Cerrar');close.clicked.connect(self.accept);row.addWidget(close);layout.addLayout(row)
        self.sheet.currentTextChanged.connect(self.clear_comparison);self.tabs.currentChanged.connect(self.update_filters);self.status_filter.currentIndexChanged.connect(self.render);self.search.textChanged.connect(self.render);self.update_filters()

    def clear_comparison(self,*_):
        self.comparison=[];self.file_rows=[];self.invalid_rows=[];self.invalid.clear()
        self.update_filters()
        if self.filename:self.file_status.setText(Path(self.filename).name+' · hoja '+self.sheet.currentText()+' · pendiente de comparar.')

    def update_filters(self,*_):
        data=[row for row in self.comparison if row['old'] in self.by_old] if self.tabs.currentIndex()==1 else self.proposal
        self.status_filter.blockSignals(True);self.status_filter.clear();self.status_filter.addItem('Todos los resultados','')
        for status in sorted({row['status'] for row in data}):self.status_filter.addItem(status,status)
        self.status_filter.blockSignals(False);self.render()

    @staticmethod
    def code(value):
        return f'{int(value):04d}' if value is not None else 'Sin referencia'

    @classmethod
    def following(cls,value):
        return cls.code(value+1) if value is not None and value<9999 else 'Agotado' if value is not None else 'Sin referencia'

    def enriched(self,row):
        target=self.by_old[row['old']];maximum=self.prefix_max.get(row['old'][:13]);terrain=target.get('base_t')
        return dict(row,base_m=self.code(maximum),next_m=self.following(maximum),base_t=self.code(terrain),next_t=self.following(terrain))

    def visible_data(self,name):
        data=self.proposal if name=='Propuesta' else self.comparison
        selected=self.status_filter.currentData() or '';needle=self.search.text().strip().casefold()
        active=self.tabs.tabText(self.tabs.currentIndex())
        rows=[]
        for original in data:
            if original['old'] not in self.by_old:continue
            row=self.enriched(original)
            if selected and name==active and row['status']!=selected:continue
            if needle and needle not in ' '.join(str(value) for value in row.values()).casefold():continue
            if any(query.casefold() not in str(row.get(self.fields[name][column][1],'')).casefold() for column,query in self.column_filters[name].items()):continue
            rows.append(row)
        return rows

    def set_column_filter(self,name,column,query):
        query=query.strip()
        if query:self.column_filters[name][column]=query
        else:self.column_filters[name].pop(column,None)
        self.render()

    def clear_column_filters(self):
        self.column_filters={'Propuesta':{},'Comparación':{}};self.render()

    def open_column_filter(self,name,column):
        from qgis.PyQt.QtGui import QCursor
        menu=QMenu(self);menu.addAction('Filtrar: '+self.fields[name][column][0]).setEnabled(False)
        widget=QComboBox(menu);widget.setEditable(True);widget.addItem('')
        values=sorted({str(self.enriched(row).get(self.fields[name][column][1],'')) for row in (self.proposal if name=='Propuesta' else self.comparison) if row['old'] in self.by_old})
        widget.addItems(values[:200]);widget.setCurrentText(self.column_filters[name].get(column,''));widget.setMinimumWidth(320)
        action=QWidgetAction(menu);action.setDefaultWidget(widget);menu.addAction(action)
        def apply():self.set_column_filter(name,column,widget.currentText());menu.close()
        menu.addAction('Aplicar (contiene)',apply);menu.addAction('Limpiar esta columna',lambda:self.set_column_filter(name,column,''))
        widget.lineEdit().returnPressed.connect(apply);widget.setFocus();menu.exec_(QCursor.pos())

    def group_summary(self,rows):
        from collections import defaultdict
        groups=defaultdict(list)
        for row in rows:groups[row['old'][:13]].append(row)
        result=[]
        for prefix,items in sorted(groups.items()):
            maximum=self.prefix_max.get(prefix)
            result.append({'prefix9':prefix[:9],'part10_13':prefix[9:13],'prefix13':prefix,
                'count':len({row['old'] for row in items}),'max_m':self.code(maximum),'next_m':self.following(maximum),
                'blocks':len({row['old'][:17] for row in items})})
        return result

    def render(self,*_):
        from qgis.PyQt.QtGui import QColor
        for name,fields in self.fields.items():
            tree=self.views[name];tree.setUpdatesEnabled(False);tree.clear()
            roots={};children={};rows=self.visible_data(name)
            group_info={item['prefix13']:item for item in self.group_summary(rows)}
            for row in rows:
                old=row['old'];prefix9=old[:9];prefix13=old[:13]
                if prefix9 not in roots:
                    values=['']*len(fields);values[0]='1–9: '+prefix9
                    values[1]='Ver subgrupos 10–13'
                    root=QTreeWidgetItem(values);tree.addTopLevelItem(root);roots[prefix9]=root
                    root.setToolTip(0,'El máximo se aplica por prefijo completo 1–13; despliegue sus subgrupos.')
                if prefix13 not in children:
                    info=group_info[prefix13];values=['']*len(fields);values[0]='10–13: '+prefix13[9:13]
                    for index,(_,key) in enumerate(fields):
                        if key=='status':values[index]=f'{info["count"]} provisionales'
                        elif key=='base_m':values[index]=info['max_m']
                        elif key=='next_m':values[index]=info['next_m']
                        elif key in ('base_t','next_t'):values[index]='Por manzana/vereda'
                    child=QTreeWidgetItem(values);child.setToolTip(0,'Prefijo completo 1–13: '+prefix13);roots[prefix9].addChild(child);children[prefix13]=child
                item=QTreeWidgetItem(['' if row.get(key) is None else str(row.get(key,'')) for _,key in fields])
                color='#217346' if row['status']=='Coincide' else '#BE594D' if row['status'] in ('Diferencia','Provisional duplicado en archivo','Definitivo duplicado en archivo') else '#9B6400' if 'Pendiente' in row['status'] or row['status']=='Falta en archivo' else '#17324D'
                for column in range(len(fields)):item.setForeground(column,QColor(color))
                children[prefix13].addChild(item)
            # Show the two territorial levels first; individual provisional NPNs stay collapsed.
            for root in roots.values():root.setExpanded(True)
            for prefix9,root in roots.items():
                for column,(_,key) in enumerate(fields):
                    if key=='status':root.setText(column,str(sum(info['count'] for prefix,info in group_info.items() if prefix.startswith(prefix9)))+' provisionales')
                    if key in ('base_m','next_m'):
                        subgroups=[info for prefix,info in group_info.items() if prefix.startswith(prefix9)]
                        root.setText(column,subgroups[0]['max_m' if key=='base_m' else 'next_m'] if len(subgroups)==1 else 'Ver subgrupos 10–13')
            for column,(label,_) in enumerate(fields):
                active=self.column_filters[name].get(column,'');tree.headerItem().setText(column,label+(' [filtro] ▾' if active else ' ▾'));tree.headerItem().setToolTip(column,'Contiene: '+active if active else 'Pulse para filtrar esta columna')
                tree.resizeColumnToContents(column)
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
            counts=Counter(row['status'] for row in self.comparison if row['old'] in self.by_old)
            omitted=sum(row['old'] not in self.by_old for row in self.comparison)
            self.file_status.setText(Path(filename).name+' · hoja '+sheet+' · '+' · '.join(f'{key}: {count}' for key,count in sorted(counts.items()))+f' · Filas inválidas: {len(invalid)} · Fuera del alcance omitidos: {omitted}')
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
            for status,count in sorted(Counter(r['status'] for r in self.proposal).items()):summary.append(['Propuesta completa · '+status,count])
            for status,count in sorted(Counter(r['status'] for r in self.visible_data('Propuesta')).items()):summary.append(['Propuesta visible · '+status,count])
            for status,count in sorted(Counter(r['status'] for r in self.visible_data('Comparación')).items()):summary.append(['Comparación · '+status,count])
            sheet=book.create_sheet('Renumeracion');sheet.append(['Nuevo esperado','Provisional','Resultado','Observación'])
            for row in self.visible_data('Propuesta'):sheet.append([row['new'],row['old'],row['status'],row['reason']])
            audit=book.create_sheet('Bases R1');audit.append([label for label,_ in PROPOSAL_FIELDS])
            for row in self.visible_data('Propuesta'):audit.append([row.get(key) for _,key in PROPOSAL_FIELDS])
            sheet=book.create_sheet('Comparacion');sheet.append([label for label,_ in COMPARE_FIELDS])
            for row in self.visible_data('Comparación'):sheet.append([row.get(key) for _,key in COMPARE_FIELDS])
            groups=book.create_sheet('Grupos y maximos R1');groups.append(['Vista','Prefijo 1–9','Código 10–13','Prefijo completo 1–13','Provisionales','Máximo manzana/vereda R1','Inicio manzana/vereda','Manzanas/veredas'])
            for name in self.fields:
                for item in self.group_summary(self.visible_data(name)):groups.append([name,item['prefix9'],item['part10_13'],item['prefix13'],item['count'],item['max_m'],item['next_m'],item['blocks']])
            summary.append(['Fuera del alcance omitidos',sum(row['old'] not in self.by_old for row in self.comparison)]);summary.append(['Vista del filtro de resultado',self.tabs.tabText(self.tabs.currentIndex())]);summary.append(['Filtros de columnas',str(self.column_filters)]);summary.append(['Búsqueda',self.search.text()]);summary.append(['Filtro de resultado',self.status_filter.currentText()])
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
