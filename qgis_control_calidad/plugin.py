from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction, QDockWidget
from qgis.PyQt.QtGui import QIcon
from pathlib import Path

from .dialog import ControlCalidadDialog


class ControlCalidadPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None
        self.dock = None

    def initGui(self):
        icon = QIcon(str(Path(__file__).resolve().parent / "icon.svg"))
        self.action = QAction(icon, "Validador Consistencia Lógica Alfanumérica", self.iface.mainWindow())
        self.action.setWhatsThis("Validar la consistencia lógica alfanumérica")
        self.action.triggered.connect(self.open_dialog)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToDatabaseMenu("Validador Consistencia Lógica Alfanumérica", self.action)

    def unload(self):
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None
            self.dialog = None
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginDatabaseMenu("Validador Consistencia Lógica Alfanumérica", self.action)

    def open_dialog(self):
        if self.dock is None:
            self.dock = QDockWidget("Validador Consistencia Lógica Alfanumérica", self.iface.mainWindow())
            self.dock.setObjectName("ValidadorConsistenciaLogicaAlfanumerica")
            self.dock.setAllowedAreas(
                Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea |
                Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
            )
            self.dock.setFeatures(
                QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
            )
            self.dialog = ControlCalidadDialog(self.dock, self.iface)
            self.dock.setWidget(self.dialog)
            self.dock.setMinimumWidth(360)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
            self.iface.mainWindow().resizeDocks([self.dock], [420], Qt.Horizontal)
        self.dock.show()
        self.dock.raise_()
