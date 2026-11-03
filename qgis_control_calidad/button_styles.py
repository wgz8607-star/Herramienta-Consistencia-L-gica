"""Disabled button appearance without altering enabled colors."""
from qgis.PyQt.QtWidgets import QPushButton, QToolButton

DISABLED_STYLE = 'QPushButton:disabled, QToolButton:disabled { background: #E9ECEF; color: #7B8490; border-color: #D8DDE3; }'

def style_disabled_buttons(widget):
    for button in widget.findChildren(QPushButton) + widget.findChildren(QToolButton):
        original = button.styleSheet()
        if original and '{' not in original:
            original = 'QPushButton, QToolButton {' + original + '}'
        if DISABLED_STYLE not in original:
            button.setStyleSheet(original + '\n' + DISABLED_STYLE)
