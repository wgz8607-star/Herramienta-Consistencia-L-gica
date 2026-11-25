"""Consistent visual emphasis for provisional identifiers and their counts."""
import re
from html import escape
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QLabel

BACKGROUND='#FFF1CC'
FOREGROUND='#8A4B00'
PATTERN=re.compile(r'\bprovisionales?\b(?:\s+en la propuesta)?(?:\s*:\s*[0-9.,]+)?',re.IGNORECASE)


def highlighted_text(text):
    parts=[];last=0
    for match in PATTERN.finditer(text):
        parts.append(escape(text[last:match.start()]))
        parts.append(f'<span style="background-color:{BACKGROUND};color:{FOREGROUND};font-weight:700;">{escape(match.group())}</span>')
        last=match.end()
    parts.append(escape(text[last:]))
    return ''.join(parts).replace('\n','<br/>')


class ProvisionalLabel(QLabel):
    def __init__(self,text='',parent=None):
        super().__init__(parent);self.setTextFormat(Qt.RichText);self.setText(text)
    def setText(self,text):
        self.plain_text=text
        super().setText(highlighted_text(text))


def emphasize_item(item,column):
    item.setBackground(column,QColor(BACKGROUND));item.setForeground(column,QColor(FOREGROUND))
    font=item.font(column);font.setBold(True);item.setFont(column,font)


def emphasize_workbook(book):
    from openpyxl.styles import PatternFill,Font
    for sheet in book:
        columns=[cell.column for cell in sheet[1] if str(cell.value or '').casefold() in ('provisional','provisionales','predios a renumerar')]
        for column in columns:
            for row in sheet.iter_rows(min_col=column,max_col=column):
                for cell in row:
                    cell.fill=PatternFill('solid',fgColor=BACKGROUND[1:]);cell.font=Font(bold=True,color=FOREGROUND[1:])
