"""Fixed-width R1/R2 references; originals are read only."""
import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import tempfile

LAYOUTS = {
    'R1': (312, [
        ('numero_predial', 1, 30), ('tipo_registro', 31, 31),
        ('no_orden', 32, 34), ('total_registro', 35, 37),
        ('nombre', 38, 137), ('estado_civil', 138, 138),
        ('tipo_documento', 139, 139), ('no_documento', 140, 151),
        ('direccion', 152, 251), ('comuna', 252, 252),
        ('destino_economico', 253, 253), ('area_terreno', 254, 268),
        ('area_construida', 269, 274), ('avaluo', 275, 289),
        ('vigencia', 290, 297), ('numero_predial_anterior', 298, 312),
    ]),
    'R2': (330, [
        ('numero_predial', 1, 30), ('tipo_registro', 31, 31),
        ('no_orden', 32, 34), ('total_registro', 35, 37),
        ('matricula_inmobiliaria', 38, 55),
        ('zona_fisica_1', 78, 80), ('zona_economica_1', 81, 83),
        ('area_terreno_1', 84, 98), ('zona_fisica_2', 121, 123),
        ('zona_economica_2', 124, 126), ('area_terreno_2', 127, 141),
        ('area_construida_1', 184, 189), ('area_construida_2', 232, 237),
        ('area_construida_3', 280, 285), ('vigencia', 308, 315),
        ('numero_predial_anterior', 316, 330),
    ]),
}


def prepare_txt_reference(kind, filename, progress=None):
    from .reference_data import PreparedReference
    width, layout = LAYOUTS[kind]
    source = Path(filename)
    encoding = 'utf-8-sig'
    try:
        with source.open(encoding=encoding) as stream:
            for line in stream:
                pass
    except UnicodeDecodeError:
        encoding = 'cp1252'
    directory = tempfile.TemporaryDirectory(prefix='qgis_reference_txt_')
    try:
        columns = tuple(field[0] for field in layout) + ('registro_original',)
        digest = hashlib.sha256(json.dumps(columns).encode())
        path = Path(directory.name) / 'reference.csv'
        count = 0
        with source.open(encoding=encoding, newline='') as stream, path.open('w', encoding='utf-8', newline='') as output:
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            for number, raw in enumerate(stream, 1):
                line = raw.rstrip('\r\n')
                if not line.strip():
                    continue
                if len(line) != width:
                    raise ValueError(f'{kind}, línea {number}: se esperaban {width} caracteres y se encontraron {len(line)}.')
                if not line[:30].isascii() or not line[:30].isdigit() or line[30] != kind[1]:
                    raise ValueError(f'{kind}, línea {number}: NPN de 30 dígitos o tipo de registro no válido.')
                if '\x00' in line:
                    raise ValueError(f'{kind}, línea {number}: carácter nulo no admitido.')
                values = []
                for name, start, end in layout:
                    value = line[start - 1:end].strip()
                    if value and (name.startswith('area_') or name == 'avaluo'):
                        try:
                            numeric = Decimal(value.replace(',', '.'))
                            if not numeric.is_finite():
                                raise InvalidOperation()
                            value = format(numeric, 'f')
                        except InvalidOperation:
                            raise ValueError(f'{kind}, línea {number}: {name} no es numérico.')
                    values.append(value)
                values.append(line)
                writer.writerow(values)
                digest.update(json.dumps(values, ensure_ascii=False, separators=(',', ':')).encode())
                digest.update(b'\n')
                count += 1
                if progress and count % 1000 == 0:
                    progress(kind, count)
        if not count:
            raise ValueError(f'{kind}: el TXT no contiene registros.')
        from .r1_unification import unify_r1
        return unify_r1(PreparedReference(kind, source.name, columns, count, digest.hexdigest(), path, directory), progress)
    except Exception:
        directory.cleanup()
        raise
