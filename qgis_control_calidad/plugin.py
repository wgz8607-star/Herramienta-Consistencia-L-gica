from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from pathlib import Path

from .dialog import ControlCalidadDialog


class ControlCalidadPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self):
        icon = QIcon(str(Path(__file__).resolve().parent / "icon.svg"))
        self.action = QAction(icon, "Validador Consistencia Lógica Alfanumérica", self.iface.mainWindow())
        self.action.setWhatsThis("Ejecutar reglas de calidad para CICA y Modelo Interno 1.0")
        self.action.triggered.connect(self.open_dialog)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToDatabaseMenu("Validador Consistencia Lógica Alfanumérica", self.action)

    def unload(self):
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginDatabaseMenu("Validador Consistencia Lógica Alfanumérica", self.action)

    def open_dialog(self):
        if self.dialog is None:
            self.dialog = ControlCalidadDialog(self.iface.mainWindow())
        if self.dialog.isMinimized():
            self.dialog.showNormal()
        else:
            self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
