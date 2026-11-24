from pathlib import Path
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon


class MaximaPlugin:
    def __init__(self,iface):self.iface=iface;self.action=None;self.dialog=None;self.reference_dialog=None
    def initGui(self):
        from .dialog import MaximaDialog
        from .candidate_dialog import CandidateDialog
        self.action=QAction(QIcon(str(Path(__file__).parent/'icon.svg')),'Renumeración predial',self.iface.mainWindow())
        def show():
            if self.dialog is None:
                self.reference_dialog=MaximaDialog(self.iface.mainWindow())
                self.dialog=CandidateDialog(self.reference_dialog,self.iface.mainWindow())
            self.dialog.showMaximized();self.dialog.raise_();self.dialog.activateWindow()
        self.action.triggered.connect(show)
        self.iface.addPluginToDatabaseMenu('Renumeración predial',self.action);self.iface.addToolBarIcon(self.action)
    def unload(self):
        if self.dialog:self.dialog.close()
        if self.reference_dialog:self.reference_dialog.close()
        if self.action:
            self.iface.removePluginDatabaseMenu('Renumeración predial',self.action);self.iface.removeToolBarIcon(self.action)
