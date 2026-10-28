"""Standalone Tk interface; all database work runs outside the UI thread."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from . import __version__
from .repositorio import COLUMNS, TABLES, TEMPLATE
from . import servicio


class AdministratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Administrador del repositorio de reglas · ' + __version__)
        self.root.geometry('1180x780'); self.root.minsize(960, 660)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.busy = False; self.plan = None; self.widgets = []
        self.host = tk.StringVar(value='172.19.3.225')
        self.port = tk.StringVar(value='5432')
        self.database = tk.StringVar(value='sentencias')
        self.user = tk.StringVar(); self.password = tk.StringVar()
        self.ssl = tk.StringVar(value='prefer')
        self.destination = tk.StringVar(value='public.' + TABLES[0])
        self.filename = tk.StringVar()
        self.summary = tk.StringVar(value='Seleccione el destino y el Excel. No se modifica la base durante la vista previa.')
        self._build()
        for variable in (self.host, self.port, self.database, self.user, self.password, self.ssl, self.destination):
            variable.trace_add('write', self.invalidate)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def _build(self):
        style = ttk.Style(self.root)
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground='#0468A3')
        style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'), padding=7)
        outer = ttk.Frame(self.root, padding=12); outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='Administrador de reglas', style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text='Programa independiente de QGIS · Carga de sentencias desde Excel').pack(anchor='w', pady=(0, 8))
        connection = ttk.LabelFrame(outer, text='Conexión del administrador', padding=8); connection.pack(fill='x')
        for row, label, variable, column, secret in (
            (0, 'Servidor', self.host, 0, False), (0, 'Puerto', self.port, 2, False), (0, 'Base de datos', self.database, 4, False),
            (1, 'Usuario', self.user, 0, False), (1, 'Contraseña', self.password, 2, True),
        ):
            ttk.Label(connection, text=label).grid(row=row, column=column, padx=(0, 5), pady=4, sticky='w')
            entry = ttk.Entry(connection, textvariable=variable, show='•' if secret else '', width=16 if column == 2 else 28)
            entry.grid(row=row, column=column+1, padx=(0, 12), pady=4, sticky='ew')
            self.widgets.append((entry, 'normal'))
        ttk.Label(connection, text='SSL').grid(row=1, column=4, sticky='w')
        ssl = ttk.Combobox(connection, textvariable=self.ssl, values=('prefer', 'require', 'verify-full', 'disable'), state='readonly', width=18)
        ssl.grid(row=1, column=5, sticky='ew', padx=(0, 12)); self.widgets.append((ssl, 'readonly'))
        connection.columnconfigure(1, weight=2); connection.columnconfigure(5, weight=2); connection.columnconfigure(3, weight=1)
        actions = ttk.Frame(outer); actions.pack(fill='x', pady=8)
        self.button(actions, 'Probar conexión', self.test_connection).pack(side='left')
        ttk.Label(actions, text='   Tabla de destino').pack(side='left', padx=8)
        destination = ttk.Combobox(actions, textvariable=self.destination, values=['public.' + table for table in TABLES], state='readonly', width=43)
        destination.pack(side='left', fill='x', expand=True); self.widgets.append((destination, 'readonly'))
        tools = ttk.Frame(outer); tools.pack(fill='x', pady=(0, 8))
        self.button(tools, 'Guardar plantilla vacía', self.save_template).pack(side='left', padx=(0, 8))
        self.button(tools, 'Exportar todas las reglas', self.export).pack(side='left', padx=(0, 8))
        self.button(tools, 'Seleccionar Excel y revisar', self.preview).pack(side='left')
        path = ttk.Entry(outer, textvariable=self.filename, state='readonly'); path.pack(fill='x', pady=(0, 5)); self.widgets.append((path, 'readonly'))
        ttk.Label(outer, textvariable=self.summary, wraplength=1120).pack(fill='x', pady=(0, 5))
        table_frame = ttk.Frame(outer); table_frame.pack(fill='both', expand=True)
        columns = ('fila', 'version', 'componente', 'codigo', 'tipo', 'activa', 'orden', 'estado')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8, selectmode='browse')
        for column, label, width in zip(columns, ('Fila', 'Versión', 'Componente', 'Código', 'Tipo', 'Activa', 'Orden', 'Resultado'), (45, 130, 135, 100, 120, 60, 60, 280)):
            self.tree.heading(column, text=label); self.tree.column(column, width=width, minwidth=45, stretch=column == 'estado')
        vertical = ttk.Scrollbar(table_frame, command=self.tree.yview); vertical.pack(side='right', fill='y')
        horizontal = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview); horizontal.pack(side='bottom', fill='x')
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.pack(fill='both', expand=True); self.tree.bind('<<TreeviewSelect>>', self.show_rule)
        detail = ttk.Notebook(outer); detail.pack(fill='x', pady=8)
        self.sql_text = self.text_tab(detail, 'Sentencia SQL')
        self.metadata_text = self.text_tab(detail, 'Todos los campos')
        self.activity = self.text_tab(detail, 'Actividad y mensajes')
        footer = ttk.Frame(outer); footer.pack(fill='x')
        self.progress = ttk.Progressbar(footer, mode='indeterminate', length=160); self.progress.pack(side='left', padx=(0, 10))
        ttk.Label(footer, text='Solo se incorporan reglas nuevas. Las existentes se conservan.').pack(side='left', fill='x', expand=True)
        self.apply_button = self.button(footer, 'Cargar reglas nuevas', self.apply)
        self.apply_button.pack(side='right'); self.apply_button.configure(state='disabled')
        self.log('Listo. La contraseña se utiliza durante la sesión y no se guarda en archivos.')

    def button(self, parent, text, command):
        widget = ttk.Button(parent, text=text, command=command, style='Action.TButton')
        self.widgets.append((widget, 'normal'))
        return widget

    def text_tab(self, notebook, label):
        frame = ttk.Frame(notebook); notebook.add(frame, text=label)
        text = ScrolledText(frame, height=7, wrap='word', font=('Consolas', 10), state='disabled')
        text.pack(fill='both', expand=True)
        return text

    @staticmethod
    def write_text(widget, text):
        widget.configure(state='normal'); widget.delete('1.0', 'end'); widget.insert('1.0', text); widget.configure(state='disabled')

    def log(self, message):
        password = self.password.get()
        if password:
            message = str(message).replace(password, '***')
        self.activity.configure(state='normal')
        self.activity.insert('end', datetime.now().strftime('%H:%M:%S') + ' · ' + str(message) + '\n')
        self.activity.see('end'); self.activity.configure(state='disabled')

    def invalidate(self, *_):
        self.plan = None
        self.apply_button.configure(state='disabled')
        self.tree.delete(*self.tree.get_children())
        self.write_text(self.sql_text, ''); self.write_text(self.metadata_text, '')
        self.summary.set('Conexión o destino cambiado. Vuelva a seleccionar el Excel y revisar la carga.')

    def params(self):
        if not self.host.get().strip() or not self.database.get().strip() or not self.user.get().strip():
            raise ValueError('Indique servidor, base de datos y usuario administrador.')
        try:
            port = int(self.port.get())
            if not 1 <= port <= 65535:
                raise ValueError()
        except ValueError:
            raise ValueError('El puerto debe ser un número entre 1 y 65535.') from None
        return dict(host=self.host.get().strip(), port=port, dbname=self.database.get().strip(),
                    user=self.user.get().strip(), password=self.password.get(), sslmode=self.ssl.get())

    def error(self, error):
        message = str(error) or type(error).__name__
        password = self.password.get()
        if password:
            message = message.replace(password, '***')
        self.summary.set('La operación no se completó. Revise el mensaje y vuelva a intentarlo.')
        self.log(message); messagebox.showerror('No se completó la operación', message, parent=self.root)

    def run_task(self, work, success):
        if self.busy:
            return
        self.busy = True
        for widget, _state in self.widgets:
            widget.configure(state='disabled')
        self.progress.start(12)
        future = self.executor.submit(work)
        def poll():
            if not future.done():
                self.root.after(75, poll)
                return
            self.busy = False; self.progress.stop()
            for widget, state in self.widgets:
                widget.configure(state=state)
            self.apply_button.configure(state='normal' if self.plan and self.plan.inserts else 'disabled')
            try:
                result = future.result()
                success(result)
            except Exception as error:
                self.error(error)
        self.root.after(75, poll)

    def destination_table(self):
        return self.destination.get().split('.', 1)[1]

    def test_connection(self):
        try:
            params = self.params()
        except ValueError as error:
            self.error(error); return
        self.summary.set('Comprobando conexión…')
        def connected(result):
            message = f'Conexión correcta: base {result[0]}, usuario {result[1]}.'
            self.summary.set(message); self.log(message)
        self.run_task(partial(servicio.check_connection, params), connected)

    def save_path(self, filename):
        return filedialog.asksaveasfilename(parent=self.root, title='Guardar Excel de reglas', initialfile=filename,
                                          defaultextension='.xlsx', filetypes=[('Excel', '*.xlsx')])

    def save_template(self):
        filename = self.save_path('plantilla_reglas.xlsx')
        if filename:
            try:
                shutil.copyfile(TEMPLATE, filename)
                self.summary.set('Plantilla guardada: ' + filename); self.log(self.summary.get())
            except Exception as error:
                self.error(error)

    def export(self):
        try:
            params = self.params()
        except ValueError as error:
            self.error(error); return
        table = self.destination_table()
        filename = self.save_path(table + '.xlsx')
        if filename:
            self.summary.set('Exportando todas las filas de la tabla…')
            def exported(count):
                self.summary.set(f'Exportadas {count} reglas, incluidas inactivas y versiones no publicadas: {filename}')
                self.log(self.summary.get())
            self.run_task(partial(servicio.export_existing, params, table, filename), exported)

    def preview(self):
        try:
            params = self.params()
        except ValueError as error:
            self.error(error); return
        filename = filedialog.askopenfilename(parent=self.root, title='Seleccione el Excel de reglas', filetypes=[('Excel', '*.xlsx')])
        if not filename:
            return
        self.invalidate(); self.filename.set(filename); self.summary.set('Leyendo Excel y preparando vista previa…')
        self.run_task(partial(servicio.inspect_file, params, self.destination_table(), filename), self.show_plan)

    def show_plan(self, plan):
        self.plan = plan
        for index, (rule, state) in enumerate(zip(plan.rules, plan.states)):
            values = rule.values
            self.tree.insert('', 'end', iid=str(index), values=(rule.row, values[0], values[1], values[2], values[3],
                             'Sí' if values[6] else 'No', values[7], state))
        publications = {record[0]: record[9] for record in plan.inserts}
        publication_text = '; '.join(version + ': ' + ('publicada' if published else 'sin publicar') for version, published in sorted(publications.items()))
        self.summary.set(f'{len(plan.rules)} filas · {len(plan.inserts)} nuevas · {len(plan.rules)-len(plan.inserts)} existentes que se conservarán. ' + publication_text)
        self.log(self.summary.get())
        self.apply_button.configure(state='normal' if plan.inserts else 'disabled')
        if plan.rules:
            self.tree.selection_set('0'); self.tree.focus('0'); self.show_rule()

    def show_rule(self, _event=None):
        selection = self.tree.selection()
        if self.plan is None or not selection:
            return
        rule = self.plan.rules[int(selection[0])]
        self.write_text(self.sql_text, rule.values[4])
        text = '\n\n'.join(name + ':\n' + (str(value) if value is not None else '(sin indicar)') for name, value in zip(COLUMNS, rule.values))
        text += '\n\nResultado: ' + self.plan.states[int(selection[0])]
        if self.plan.states[int(selection[0])] == 'Nueva':
            effective = next(record for record in self.plan.inserts if record[:3] == rule.key)
            text += '\nMetadatos que se guardarán:\ndescripcion_version: ' + str(effective[8]) + '\nversion_publicada: ' + ('Sí' if effective[9] else 'No')
        self.write_text(self.metadata_text, text)

    def apply(self):
        if self.busy or not self.plan or not self.plan.inserts:
            return
        try:
            params = self.params()
        except ValueError as error:
            self.error(error); return
        plan = self.plan
        prompt = (f'Servidor: {params["host"]}\nBase: {params["dbname"]}\nDestino: public.{plan.table}\n\n'
                  f'Se incorporarán {len(plan.inserts)} reglas nuevas. Las existentes no se modificarán y el SQL no se ejecutará.\n\n¿Confirma la carga?')
        if not messagebox.askyesno('Confirmar carga revisada', prompt, parent=self.root, default='no'):
            return
        self.invalidate(); self.summary.set('Cargando reglas revisadas…')
        def loaded(count):
            self.summary.set(f'{count} reglas incorporadas correctamente en public.{plan.table}.')
            self.log(self.summary.get())
            messagebox.showinfo('Carga terminada', self.summary.get(), parent=self.root)
        self.run_task(partial(servicio.apply_plan, params, plan), loaded)

    def close(self):
        if self.busy:
            messagebox.showinfo('Proceso en curso', 'Espere a que termine la operación antes de cerrar.', parent=self.root)
            return
        self.password.set('')
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


def main():
    root = tk.Tk()
    AdministratorApp(root)
    root.mainloop()
