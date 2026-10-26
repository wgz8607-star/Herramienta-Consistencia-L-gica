"""Human review independent of QGIS and of the automatic validation outcome."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile
import unicodedata
from zoneinfo import ZoneInfo

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.worksheet.datavalidation import DataValidation

PENDING = "Revisión pendiente"
EXCEPTION = "Excepción"
ADJUST = "Solicitar ajuste"
STATES = (PENDING, EXCEPTION, ADJUST)
FORMAT = "revision-catastral-1"
REVIEW_FIELDS = ("estado_revision_usuario", "observacion_usuario", "fecha_revision_usuario")
# These are explicitly positional fields, not object identifiers such as id/t_id.
POSITION_FIELDS = {"row_number", "row_num", "rownum", "numero_fila", "nro_fila", "fila_reporte"}


def valid_observation(value):
    return isinstance(value, str) and any(
        not c.isspace() and unicodedata.category(c)[0] not in "CZ" for c in value
    )


def canonical(value):
    """Retain SQL types and exact strings (including leading zeroes)."""
    if value is None:
        return ["null", None]
    if isinstance(value, bool):
        return ["bool", value]
    if isinstance(value, str):
        return ["str", value]
    if isinstance(value, int):
        return ["int", str(value)]
    if isinstance(value, Decimal):
        return ["decimal", str(value)]
    if isinstance(value, float):
        return ["float", repr(value)]
    if isinstance(value, (datetime, date, time)):
        return [type(value).__name__, value.isoformat()]
    if isinstance(value, (bytes, bytearray, memoryview)):
        return ["bytes", bytes(value).hex()]
    if isinstance(value, dict):
        return ["dict", [[str(k), canonical(v)] for k, v in sorted(value.items(), key=lambda x: str(x[0]))]]
    if isinstance(value, (list, tuple)):
        return ["list", [canonical(v) for v in value]]
    raise ValueError(f"Tipo de dato no compatible con recuperación segura: {type(value).__name__}")


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def display(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return dumps(canonical(value))
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    return str(value)


@dataclass
class ReviewCase:
    key: str
    identity: str
    component: str
    rule: str
    automatic: str
    data: dict
    recoverable: bool = True
    estado_revision_usuario: str = PENDING
    observacion_usuario: str = ""
    fecha_revision_usuario: str = ""

    def tracking(self):
        return tuple(getattr(self, name) for name in REVIEW_FIELDS)

    def has_tracking(self):
        return self.tracking() != (PENDING, "", "")

    def set_review(self, state, observation, timestamp=None):
        if state not in STATES:
            raise ValueError("Estado de revisión no válido.")
        if state == EXCEPTION and not valid_observation(observation):
            raise ValueError("Una Excepción requiere una Observación con texto válido.")
        if (state, observation) != self.tracking()[:2]:
            self.estado_revision_usuario = state
            self.observacion_usuario = observation
            self.fecha_revision_usuario = timestamp or datetime.now(ZoneInfo("America/Bogota")).isoformat(timespec="seconds")
            return True
        return False


def build_cases(results, context):
    cases = []
    for result in results:
        for row in result.rows or []:
            fields = {k: v for k, v in row.items() if str(k).lower() not in POSITION_FIELDS}
            has_identifier = any(
                re.search(r"(^|_)(id|tid|uuid|guid|fid|npn|nit|documento|cedula|identificacion|predio|predial|codigo)(_|$)", str(k).lower())
                and str(k).lower() not in {'codigo_regla', 'id_regla', 'codigo_validacion', 'id_validacion'}
                and v is not None and display(v).strip() for k, v in fields.items()
            )
            safe = (bool(getattr(result, "criterion_hash", ""))
                    and getattr(result, "identity_safe", True) and has_identifier)
            try:
                payload = {
                    "format": FORMAT, "context": context,
                    "validation": [result.category, result.rule],
                    "criterion": getattr(result, "criterion_hash", ""),
                    "automatic": result.status, "data": canonical(fields),
                }
                identity = dumps(payload)
            except ValueError:
                safe = False
                identity = dumps({"format": FORMAT, "unsupported": True})
            cases.append(ReviewCase(digest(identity), identity, result.category, result.rule,
                                    result.status, dict(row), safe))
    return cases


def _text(cell, value):
    value = display(value)
    if len(value) > 32767:
        raise ValueError("Un dato supera el límite de texto de Excel (32767 caracteres); no se guardó un archivo incompleto.")
    cell.value = value
    cell.data_type = "s"  # Prevent Excel formulas and numeric conversion of identifiers.
    cell.number_format = "@"


def save_review(path, cases, results=(), general_rows=()):
    for case in cases:
        if case.estado_revision_usuario not in STATES:
            raise ValueError("Estado de revisión no válido.")
        if case.estado_revision_usuario == EXCEPTION and not valid_observation(case.observacion_usuario):
            raise ValueError("No se puede guardar una Excepción sin Observación válida.")
    book = Workbook()
    sheet = book.active
    sheet.title = "Revisión"
    fields = sorted({str(k) for case in cases for k in case.data})
    headers = ["clave_caso", "componente", "validacion", "resultado_automatico", *REVIEW_FIELDS,
               "recuperable", *["dato:" + name for name in fields]]
    sheet.append(headers)
    for index, case in enumerate(cases, 2):
        values = [case.key, case.component, case.rule, case.automatic, *case.tracking(),
                  "Sí" if case.recoverable else "No", *[case.data.get(name) for name in fields]]
        for column, value in enumerate(values, 1):
            _text(sheet.cell(index, column), value)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = 28
    sheet.cell(1, 6).comment = Comment("Observación del usuario; obligatoria para Excepción.", "Validador")
    if cases:
        validation = DataValidation(type="list", formula1='"' + ','.join(STATES) + '"', allow_blank=False)
        validation.errorTitle = "Estado no válido"
        validation.error = "Seleccione un estado de revisión de la lista."
        validation.showErrorMessage = True
        validation.errorStyle = "stop"
        sheet.add_data_validation(validation)
        validation.add(f"E2:E{len(cases)+1}")
    meta = book.create_sheet("_Identidades")
    meta.append([FORMAT, "fragmento", "contenido"])
    identities = {case.key: case.identity for case in cases}
    for key, identity in identities.items():
        for part, offset in enumerate(range(0, len(identity), 30000)):
            meta.append([key, part, identity[offset:offset+30000]])
            for cell in (meta.cell(meta.max_row, 1), meta.cell(meta.max_row, 3)):
                cell.data_type = 's'
    meta.sheet_state = "hidden"
    context_sheet = book.create_sheet("Contexto")
    context_sheet.append(["Campo", "Valor"])
    if cases:
        context = json.loads(cases[0].identity).get('context', {})
        for row, (name, value) in enumerate(sorted(context.items()), 2):
            _text(context_sheet.cell(row, 1), name)
            _text(context_sheet.cell(row, 2), value)
    execution = book.create_sheet("Ejecución automática")
    execution.append(["Componente", "Validación", "Resultado automático", "Hallazgos", "Detalle técnico", "Descripción"])
    for result in results:
        execution.append([None] * 6)
        for col, value in enumerate([result.category, result.rule, result.status, result.findings, result.detail, result.description], 1):
            _text(execution.cell(execution.max_row, col), value)
    if general_rows:
        general = book.create_sheet("Reporte general")
        columns = sorted({str(k) for row in general_rows for k in row})
        general.append(columns)
        for row_index, row in enumerate(general_rows, 2):
            for col, name in enumerate(columns, 1):
                _text(general.cell(row_index, col), row.get(name))
    # Write atomically: a failed save must not replace the last saved review.
    path = Path(path)
    handle, temporary = tempfile.mkstemp(suffix=".xlsx", dir=path.parent)
    os.close(handle)
    try:
        book.save(temporary)
        os.replace(temporary, path)
    finally:
        book.close()
        if os.path.exists(temporary):
            os.unlink(temporary)


@dataclass
class ImportedReview:
    key: str
    state: str
    observation: str
    timestamp: str
    recoverable: bool
    valid: bool = True


def load_review(path):
    book = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    try:
        if "_Identidades" not in book or "Revisión" not in book:
            raise ValueError("Este archivo no es una revisión guardada por la herramienta; los reportes anteriores no contienen una clave segura.")
        meta = book["_Identidades"]
        if meta.cell(1, 1).value != FORMAT:
            raise ValueError("Formato de revisión no compatible.")
        chunks = defaultdict(dict)
        for key, part, content in meta.iter_rows(min_row=2, max_col=3, values_only=True):
            if key is None:
                continue
            if not isinstance(part, int) or part < 0 or part in chunks[key] or not isinstance(content, str):
                raise ValueError("Metadatos de identidad duplicados o dañados.")
            chunks[key][part] = content
        identities = {}
        for key, pieces in chunks.items():
            if sorted(pieces) != list(range(len(pieces))):
                raise ValueError("Identidad incompleta.")
            identity = ''.join(pieces[i] for i in range(len(pieces)))
            if digest(identity) != key:
                raise ValueError("Identidad de caso alterada.")
            identities[key] = json.loads(identity)
        sheet = book["Revisión"]
        headers = [c.value for c in next(sheet.iter_rows(max_row=1))]
        required = ["clave_caso", "componente", "validacion", "resultado_automatico", *REVIEW_FIELDS, "recuperable"]
        if any(headers.count(name) != 1 for name in required) or len(headers) != len(set(headers)):
            raise ValueError("Faltan columnas obligatorias o hay columnas duplicadas.")
        records = []
        for cells in sheet.iter_rows(min_row=2):
            row = dict(zip(headers, [c.value for c in cells]))
            if not any(value is not None for value in row.values()):
                continue
            key = row.get("clave_caso")
            payload = identities.get(key)
            valid = payload is not None and not any(c.data_type == "f" for c in cells)
            if valid and not payload.get("unsupported"):
                original = dict(payload["data"][1])
                actual = {h[5:]: '' if row[h] is None else str(row[h]) for h in headers if str(h).startswith('dato:') and h[5:].lower() not in POSITION_FIELDS}
                expected = {k: _display_canonical(v) for k, v in original.items()}
                # Blank columns from other rules are harmless; changed data is not.
                valid = all(actual.get(k) == v for k, v in expected.items()) and not any(v for k, v in actual.items() if k not in expected)
                valid = valid and [row['componente'], row['validacion']] == payload['validation'] and row['resultado_automatico'] == payload['automatic']
            records.append(ImportedReview(key, str(row[REVIEW_FIELDS[0]] or PENDING),
                                          str(row[REVIEW_FIELDS[1]] or ''), str(row[REVIEW_FIELDS[2]] or ''),
                                          row.get('recuperable') == 'Sí', valid))
        return records
    finally:
        book.close()


def _display_canonical(value):
    kind, data = value
    if kind == 'null':
        return ''
    if kind == 'bool':
        return str(data)
    if kind in ('dict', 'list'):
        return dumps(value)
    return str(data)


def restore_review(cases, records):
    current_counts = Counter(case.key for case in cases)
    old_counts = Counter(record.key for record in records)
    current = {case.key: case for case in cases}
    counts = dict(incorporadas=0, sin_correspondencia=0, ambiguas=0, conflictos=0,
                  excepciones_invalidas=0, estados_invalidos=0, datos_invalidos=0, sin_seguimiento=0)
    for record in records:
        if not record.valid or not record.recoverable:
            counts['datos_invalidos'] += 1
            continue
        if record.key not in current:
            counts['sin_correspondencia'] += 1
            continue
        case = current[record.key]
        if current_counts[record.key] != 1 or old_counts[record.key] != 1 or not case.recoverable:
            counts['ambiguas'] += 1
            continue
        state = record.state
        if state not in STATES:
            state = PENDING
            counts['estados_invalidos'] += 1
        if state == EXCEPTION and not valid_observation(record.observation):
            state = PENDING
            counts['excepciones_invalidas'] += 1
        tracking = (state, record.observation, record.timestamp)
        if case.has_tracking():
            if case.tracking() != tracking:
                counts['conflictos'] += 1
            continue
        if tracking == (PENDING, '', ''):
            counts['sin_seguimiento'] += 1
            continue
        for name, value in zip(REVIEW_FIELDS, tracking):
            setattr(case, name, value)
        counts['incorporadas'] += 1
    return counts
