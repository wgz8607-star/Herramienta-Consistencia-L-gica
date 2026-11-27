from qgis.PyQt.QtWidgets import QDialog,QVBoxLayout,QLabel,QCheckBox,QDialogButtonBox


class CicaProvisionalOptions(QDialog):
    def __init__(self,selected='789',parent=None):
        super().__init__(parent);self.setWindowTitle('CICA · Confirmar series provisionales')
        layout=QVBoxLayout(self);layout.addWidget(QLabel('Antes de comprobar, indique por separado qué series son provisionales\nen las posiciones 14 y 18.'))
        self.seven=QCheckBox('7xxx son provisionales');self.seven.setChecked('7' in selected);layout.addWidget(self.seven)
        self.eight=QCheckBox('8xxx son provisionales');self.eight.setChecked('8' in selected);layout.addWidget(self.eight)
        layout.addWidget(QLabel('9xxx siempre se considera provisional.\nLas series desmarcadas conservan su numeración.'))
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Ok).setText('3.1 Confirmar criterios');buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)

    def prefixes(self):
        return ('7' if self.seven.isChecked() else '')+('8' if self.eight.isChecked() else '')+'9'
