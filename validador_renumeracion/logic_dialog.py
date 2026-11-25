"""User-facing explanation of the rules implemented by the renumbering engine."""
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog,QVBoxLayout,QLabel,QTextBrowser,QDialogButtonBox
from .build_info import TITLE

LOGIC_HTML='''
<html><head><style>
body {font-family: sans-serif; color:#17324D; font-size:13px;}
h2 {color:#0066B3; margin-top:20px;} h3 {color:#0066B3;}
table {border-collapse:collapse;} th,td {border:1px solid #D9E5EF; padding:8px;}
th {background:#E8F1FA;} .provisional {background:#FFF1CC;color:#8A4B00;font-weight:bold;}
</style></head><body>
<h2>1. Fuente y provisionales</h2>
<p><b>CICA:</b> copia <code>sentencias.snc_cica_copy.cica_predio</code>, municipio seleccionado,
con <b>etapa VALIDADO</b> y <b>estado_control DESCARGADO_AL_SNC</b>.
El estado se toma de <b>cica_predio.estado</b>.</p>
<p><b>Modelo Interno:</b> esquema seleccionado. Es CANCELADO si alguna novedad asociada contiene
la palabra <b>cancelación</b>, sin distinguir mayúsculas ni tilde; si no la tiene, es ACTIVO.
Si no se puede consultar esa relación, se informa SIN INFORMACIÓN.</p>
<p><span class="provisional">Provisional CICA:</span> 7, 8 o 9 en posición 14 o 18.
<span class="provisional">Provisional Modelo Interno:</span> una letra en posición 14 o 18.</p>
<h2>2. Referencia R1 y alcance</h2>
<p>Los máximos se obtienen únicamente del <b>R1 leído para el mismo municipio</b>.
Solo se propone la renumeración de las zonas seleccionadas entre los provisionales identificados.</p>
<table><tr><th>Posiciones del NPN</th><th>Uso</th></tr>
<tr><td>1–5</td><td>Municipio DIVIPOLA</td></tr>
<tr><td>6–7 / 6–9</td><td>Zona / Zona–sector</td></tr>
<tr><td>1–9 → 10–13</td><td>Agrupación visual para revisar sectores y subdivisiones</td></tr>
<tr><td>1–13</td><td>Referencia territorial para el máximo de manzana o vereda</td></tr>
<tr><td>14–17 / 1–17</td><td>Código de manzana/vereda / identificación completa de la manzana/vereda</td></tr>
<tr><td>18–21 / 1–21</td><td>Código de terreno / grupo de terreno</td></tr>
<tr><td>22 / 23–30</td><td>Condición del predio / sufijo que se conserva</td></tr></table>
<p><b>Urbano y centros poblados:</b> Manzana. <b>Rural:</b> Vereda.</p>
<h2>3. Manzanas o veredas nuevas</h2>
<p>Se agrupan por el prefijo provisional completo <b>1–17</b> y se ordenan de menor a mayor.
Cada manzana/vereda nueva recibe <b>máximo R1 + 1</b>, dentro del mismo prefijo <b>1–13</b>.
Todos sus predios reciben el mismo código definitivo 14–17.</p>
<h2>4. Terrenos y consecutivos sin saltos</h2>
<p>En una manzana/vereda existente se inicia en su <b>máximo terreno R1 + 1</b>.
En una manzana/vereda nueva se inicia en <b>0001</b>.
Los grupos de terreno se ordenan por su numeración provisional de menor a mayor.
<b>Los saltos del provisional no se trasladan al definitivo.</b></p>
<table><tr><th>Provisional</th><th>Definitivo, si el máximo es 0250</th></tr>
<tr><td class="provisional">9001</td><td>0251</td></tr>
<tr><td class="provisional">9003</td><td>0252</td></tr>
<tr><td class="provisional">9008</td><td>0253</td></tr></table>
<h2>5. Predios que comparten terreno</h2>
<ul>
<li>La condición <b>2</b> puede acompañar a un predio base de condición <b>0, 3, 4, 8 o 9</b>.
Se admite un compañero de condición 2 por terreno.</li>
<li>Se admiten <b>uno o varios predios de condición 5</b>, todos <b>CANCELADOS</b>, junto al predio base válido.
Pueden ser el segundo registro sin condición 2, con base de condición distinta de 2 y 5,
o acompañar a la pareja base + condición 2.</li>
<li>Si cualquier condición 5 está ACTIVA o su estado no está comprobado, el grupo queda <b>Pendiente</b>.</li>
<li><b>PH (9) y condominios (8):</b> sus predios con el mismo prefijo provisional <b>1–22</b>
comparten el terreno definitivo. Cada grupo consume <b>un solo consecutivo de terreno</b>,
no un número por cada unidad.</li>
<li>Los NPN idénticos se cuentan una sola vez. Estados contradictorios del mismo NPN se señalan.
La ampliación para condición 5 no habilita repeticiones arbitrarias de otras condiciones.</li>
</ul>
<h2>6. Opción de terrenos 090x del R1</h2>
<p>La casilla <b>Tomar terrenos 090x (0900–0909), condición 9, como máximos R1</b>
solo afecta a <b>18–21</b> cuando <b>22 = 9</b>.</p>
<ul><li><b>Sin marcar:</b> esos registros no elevan el máximo de terreno.</li>
<li><b>Marcada:</b> también participan en el máximo.</li></ul>
<p>La opción no cambia el máximo de manzana/vereda. Al cambiarla se recalculan la propuesta
y una comparación ya cargada; la elección se registra en Excel.</p>
<h2>7. Condición y sufijo</h2>
<p>Se conserva la <b>condición en posición 22</b> y todo el contenido de <b>23–30</b>.
La propuesta contiene el estado ACTIVO/CANCELADO obtenido de la fuente, también en la comparación y el Excel.</p>
<h2>8. Casos pendientes</h2>
<p>Sin referencia R1 suficiente, sin terreno elegible después de excluir 090x, al superar <b>9999</b>,
ante repeticiones no admitidas, condiciones 5 no canceladas o NPN definitivos que ya existan en el R1,
se indica <b>Pendiente</b> y el motivo. No se inventa un máximo ni se aprueba el caso automáticamente.</p>
<h2>9. Comparación y alcance del resultado</h2>
<p>En el Excel: <b>A = nuevo definitivo</b>, <b>B = provisional</b>, ambos como texto.
Se comparan únicamente los provisionales seleccionados. Se distinguen Coincide, Diferencia,
Falta en archivo, duplicados y Pendiente de generar.</p>
<p><b>Coincide</b> significa que el archivo coincide con la propuesta calculada.
<b>No acredita que el cambio ya esté aplicado en la base.</b> El plugin consulta y exporta;
<b>no modifica los datos de la fuente</b>.</p>
</body></html>
'''


class RenumberingLogicDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent);self.setWindowTitle('Lógica de renumeración · '+TITLE)
        self.setWindowFlags(self.windowFlags()|Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint)
        self.resize(980,800);layout=QVBoxLayout(self)
        heading=QLabel('Lógica de renumeración');heading.setStyleSheet('font-size:22px;color:#0066B3;font-weight:bold;');layout.addWidget(heading)
        layout.addWidget(QLabel(TITLE))
        if parent is not None and hasattr(parent,'take_090x'):
            policy=QLabel('Propuesta actual · 090x como máximos R1: '+('Sí' if parent.take_090x.isChecked() else 'No'))
            policy.setStyleSheet('background:#E8F1FA;padding:8px;color:#0066B3;font-weight:bold;');layout.addWidget(policy)
        self.browser=QTextBrowser();self.browser.setOpenExternalLinks(False);self.browser.setHtml(LOGIC_HTML);layout.addWidget(self.browser,1)
        buttons=QDialogButtonBox(QDialogButtonBox.Close);buttons.button(QDialogButtonBox.Close).setText('Cerrar');buttons.rejected.connect(self.reject);layout.addWidget(buttons)


def show_renumbering_logic(parent):
    RenumberingLogicDialog(parent).exec_()
