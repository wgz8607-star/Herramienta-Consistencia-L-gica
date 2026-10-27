"""Official user-supplied workbook downloads; never rewrite these files."""
from pathlib import Path
import re

DIRECTORY = Path(__file__).parent / 'resources' / 'formatos'
FORMATS = {
    'CICA': ('Formato homologado de Consistencia lógica CICA V2', 'Consistencia_logica_alfanumerica_CICA_V2.xlsx'),
    'Modelo Interno de Levantamiento 1.0': ('Formato Modelo interno V2', 'Formato_Modelo_Interno_V2.xlsx'),
}


def validation_format(model, environment, version):
    if model not in FORMATS or environment != 'Validaciones del modelo' or not version:
        return None
    identifier = version.get('id', {})
    table = identifier.get('table', '') if isinstance(identifier, dict) else ''
    # Prefer the explicit repository table version over the displayed version name.
    table_version = re.search(r'(?:^|_)v(\d+)(?:_|$)', table, re.I)
    if table_version:
        is_v2 = table_version.group(1) == '2'
    else:
        is_v2 = bool(re.match(r'^v?2(?:[_.\s-]|$)', str(version.get('codigo', '')).strip(), re.I))
    if not is_v2:
        return None
    label, filename = FORMATS[model]
    return label, DIRECTORY / filename
