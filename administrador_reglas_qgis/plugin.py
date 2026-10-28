from pathlib import Path
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from .dialog import AdministratorDialog


class AdministradorReglasPlugin:
    def __init__(self, iface):
        self.iface = iface; self.action = None; self.dialog = None

    def initGui(self):
        self.action = QAction(QIcon(str(Path(__file__).parent / 'icon.svg')), 'Administrador de Reglas SQL', self.iface.mainWindow())
        self.action.triggered.connect(self.open_dialog)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToDatabaseMenu('Administrador de Reglas SQL', self.action)

    def open_dialog(self):
        if self.dialog is None:
            self.dialog = AdministratorDialog(self.iface.mainWindow())
        if self.dialog.isMinimized():
            self.dialog.showNormal()
        else:
            self.dialog.show()
        self.dialog.raise_(); self.dialog.activateWindow()

    def unload(self):
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginDatabaseMenu('Administrador de Reglas SQL', self.action)
            self.action.deleteLater(); self.action = None
        if self.dialog:
            if self.dialog.busy:
                self.dialog.close_when_idle = True
            else:
                self.dialog.close(); self.dialog.deleteLater()
            self.dialog = None
