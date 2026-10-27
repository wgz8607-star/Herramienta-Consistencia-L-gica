"""Read-only FileGDB snapshots, installed only in a validation session's pg_temp."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import stat
import tempfile
import zipfile

from .reference_data import column_name


@dataclass
class SpatialLayer:
    table: str
    source_name: str
    columns: tuple
    types: tuple
    row_count: int
    csv_path: Path
    geometry_column: str = ''
    srid: int = 0


@dataclass
class PreparedGdb:
    filename: str
    layers: dict
    fingerprint: str
    directory: object

    def close(self):
        self.directory.cleanup()


def extract_gdb(source, directory):
    """Support .gdb directories or one .gdb inside a ZIP; never open the ZIP in place."""
    source = Path(source)
    if source.is_dir() and source.suffix.lower() == '.gdb':
        return source
    if not source.is_file() or source.suffix.lower() != '.zip':
        raise ValueError('Seleccione una carpeta .gdb o un ZIP que contenga una geodatabase.')
    destination = Path(directory).resolve()
    with zipfile.ZipFile(source) as archive:
        for entry in archive.infolist():
            path = (destination / entry.filename.replace('\\', '/')).resolve()
            if not path.is_relative_to(destination) or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError('El ZIP contiene una ruta no admitida.')
            if entry.is_dir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as input_file, path.open('wb') as output:
                    shutil.copyfileobj(input_file, output)
    candidates = sorted(p for p in destination.rglob('*') if p.is_dir() and p.suffix.lower() == '.gdb')
    if len(candidates) != 1:
        raise ValueError('El ZIP debe contener exactamente una carpeta .gdb.')
    return candidates[0]


def spatial_srid(layer):
    reference = layer.GetSpatialRef()
    if reference is None:
        return 0
    reference = reference.Clone()
    reference.AutoIdentifyEPSG()
    code = reference.GetAuthorityCode(None)
    if reference.GetAuthorityName(None) == 'EPSG' and code:
        return int(code)
    for candidate, confidence in reference.FindMatches():
        if confidence == 100 and candidate.GetAuthorityName(None) == 'EPSG':
            return int(candidate.GetAuthorityCode(None))
    return 0


def field_type(field, ogr):
    kind = field.GetType()
    if kind == ogr.OFTInteger and field.GetSubType() == ogr.OFSTBoolean:
        return 'BOOLEAN'
    return {ogr.OFTInteger: 'INTEGER', ogr.OFTInteger64: 'BIGINT', ogr.OFTReal: 'DOUBLE PRECISION',
            ogr.OFTDate: 'DATE', ogr.OFTTime: 'TIME', ogr.OFTDateTime: 'TIMESTAMP WITH TIME ZONE',
            ogr.OFTBinary: 'BYTEA', ogr.OFTIntegerList: 'JSONB', ogr.OFTInteger64List: 'JSONB',
            ogr.OFTRealList: 'JSONB', ogr.OFTStringList: 'JSONB'}.get(kind, 'TEXT')


def field_value(feature, index, pg_type):
    value = feature.GetField(index)
    if value is None:
        return None
    if pg_type in ('DATE', 'TIME', 'TIMESTAMP WITH TIME ZONE'):
        year, month, day, hour, minute, second, tz_flag = feature.GetFieldAsDateTime(index)
        if pg_type == 'DATE':
            return f'{year:04d}-{month:02d}-{day:02d}'
        time_text = f'{hour:02d}:{minute:02d}:{second:09.6f}'
        if pg_type == 'TIME':
            return time_text
        if tz_flag not in (0, 1):
            offset = (tz_flag - 100) * 15
            time_text += ('+' if offset >= 0 else '-') + f'{abs(offset)//60:02d}:{abs(offset)%60:02d}'
        return f'{year:04d}-{month:02d}-{day:02d}T{time_text}'
    if pg_type == 'BYTEA':
        return '\\x' + bytes(feature.GetFieldAsBinary(index)).hex()
    if pg_type == 'JSONB':
        return json.dumps(value, ensure_ascii=False)
    if pg_type == 'BOOLEAN':
        return 'true' if value else 'false'
    return str(value)


def write_values(stream, values):
    # Unquoted empty is SQL NULL; quoted empty is an actual empty string.
    stream.write(','.join('' if value is None else '"' + str(value).replace('"', '""') + '"' for value in values) + '\n')


def prepare_gdb(filename):
    from osgeo import gdal, ogr
    directory = tempfile.TemporaryDirectory(prefix='qgis_cica_gdb_')
    dataset = None
    try:
        gdb = extract_gdb(filename, Path(directory.name) / 'extracted')
        dataset = gdal.OpenEx(str(gdb), gdal.OF_VECTOR | gdal.OF_READONLY, allowed_drivers=['OpenFileGDB', 'FileGDB'])
        if dataset is None:
            raise ValueError('No fue posible leer la geodatabase. Compruebe que no esté incompleta o bloqueada.')
        layers = {}
        digest = hashlib.sha256()
        for layer_index in range(dataset.GetLayerCount()):
            layer = dataset.GetLayerByIndex(layer_index)
            source_name = layer.GetName()
            table = column_name(source_name, layer_index + 1)
            if table[0].isdigit():
                table = 'capa_' + table[:55]
            if table in layers or table.startswith(('pg_', 'reference_')):
                raise ValueError('Nombre de capa duplicado o reservado: ' + source_name)
            definition = layer.GetLayerDefn()
            fields = [definition.GetFieldDefn(index) for index in range(definition.GetFieldCount())]
            columns = [column_name(field.GetName(), index + 1) for index, field in enumerate(fields)]
            types = [field_type(field, ogr) for field in fields]
            fid_column = column_name(layer.GetFIDColumn() or 'fid', 1)
            add_fid = fid_column not in columns
            if add_fid:
                columns.insert(0, fid_column); types.insert(0, 'BIGINT')
            geometry_column = ''
            srid = 0
            if definition.GetGeomFieldCount():
                geometry_column = column_name(definition.GetGeomFieldDefn(0).GetName() or 'geom', len(columns) + 1)
                columns.append(geometry_column); types.append('geometry')
                srid = spatial_srid(layer)
                if not srid:
                    raise ValueError(f'{source_name}: no se identificó un código EPSG para el sistema de referencia. Defínalo en el archivo antes de cargarlo.')
            if len(columns) != len(set(columns)):
                raise ValueError(f'{source_name}: hay campos duplicados después de normalizar los nombres.')
            path = Path(directory.name) / f'layer_{layer_index}.csv'
            digest.update(json.dumps((table, columns, types, srid)).encode())
            count = 0
            layer.ResetReading()
            with path.open('w', encoding='utf-8', newline='') as output:
                for feature in layer:
                    values = ([str(feature.GetFID())] if add_fid else [])
                    values.extend(field_value(feature, index, field_type(field, ogr)) for index, field in enumerate(fields))
                    if geometry_column:
                        geometry = feature.GetGeometryRef()
                        values.append(f'SRID={srid};{geometry.ExportToIsoWkt()}' if geometry is not None else None)
                    write_values(output, values)
                    digest.update(json.dumps(values, ensure_ascii=False).encode()); digest.update(b'\n')
                    count += 1
                    feature = None
            layers[table] = SpatialLayer(table, source_name, tuple(columns), tuple(types), count, path, geometry_column, srid)
        if not layers:
            raise ValueError('La geodatabase no contiene capas o tablas legibles.')
        return PreparedGdb(Path(filename).name, layers, digest.hexdigest(), directory)
    except Exception:
        directory.cleanup()
        raise
    finally:
        layer = None
        dataset = None


def layer_definitions(layer):
    from psycopg2 import sql
    allowed_types = {'BOOLEAN', 'INTEGER', 'BIGINT', 'DOUBLE PRECISION', 'DATE', 'TIME', 'TIMESTAMP WITH TIME ZONE', 'BYTEA', 'JSONB', 'TEXT', 'geometry'}
    if any(kind not in allowed_types for kind in layer.types):
        raise ValueError('Tipo de campo de geodatabase no admitido.')
    return sql.SQL(', ').join(sql.SQL('{} {}').format(sql.Identifier(column), sql.SQL(kind)) for column, kind in zip(layer.columns, layer.types))


def install_gdb(connection, prepared, exclude=()):
    from psycopg2 import sql
    with connection.cursor() as cursor:
        for name, layer in sorted(prepared.layers.items()):
            if name in exclude:
                continue
            definitions = layer_definitions(layer)
            cursor.execute(sql.SQL('CREATE TEMP TABLE {} ({}) ON COMMIT PRESERVE ROWS').format(sql.Identifier(name), definitions))
            query = sql.SQL('COPY pg_temp.{} ({}) FROM STDIN WITH (FORMAT CSV, ENCODING \'UTF8\')').format(sql.Identifier(name), sql.SQL(', ').join(sql.Identifier(column) for column in layer.columns))
            with layer.csv_path.open(encoding='utf-8', newline='') as stream:
                cursor.copy_expert(query.as_string(connection), stream)
