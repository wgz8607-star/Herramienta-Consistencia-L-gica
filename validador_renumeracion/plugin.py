from pathlib import Path
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon


class MaximaPlugin:
    def __init__(self,iface):self.iface=iface;self.action=None;self.dialog=None
    def initGui(self):
        from .dialog import MaximaDialog
        self.action=QAction(QIcon(str(Path(__file__).parent/'icon.svg')),'Renumeración · Máximos R1',self.iface.mainWindow())
        def show():
            if self.dialog is None:self.dialog=MaximaDialog(self.iface.mainWindow())
            self.dialog.showNormal();self.dialog.raise_();self.dialog.activateWindow()
        self.action.triggered.connect(show)
        self.iface.addPluginToDatabaseMenu('Renumeración · Máximos R1',self.action);self.iface.addToolBarIcon(self.action)
    def unload(self):
        if self.dialog:self.dialog.close()
        if self.action:
            self.iface.removePluginDatabaseMenu('Renumeración · Máximos R1',self.action);self.iface.removeToolBarIcon(self.action)
