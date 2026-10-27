"""Local file freshness checks; paths and content are never sent anywhere."""
import hashlib
from pathlib import Path


def file_stat(path):
    value = Path(path).stat()
    return (value.st_size, value.st_mtime_ns, value.st_ctime_ns, value.st_ino)


def fingerprint_file(path):
    before = file_stat(path)
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    after = file_stat(path)
    if before != after:
        raise ValueError('El archivo cambió durante la lectura. Guárdelo y vuelva a cargarlo.')
    return {'stat': after, 'sha256': digest.hexdigest()}


def inspect_source(source, force=False):
    original = source.get('file_snapshot')
    if not original:
        return None
    try:
        observed = file_stat(source['path'])
        if force or observed != source.get('observed_stat') or source.get('file_state') == 'unavailable':
            current = fingerprint_file(source['path'])
            source['observed_stat'] = current['stat']
            source['file_state'] = 'modified' if current['sha256'] != original['sha256'] else 'current'
            source['file_error'] = ''
    except (OSError, ValueError) as error:
        source['file_state'] = 'unavailable'
        source['file_error'] = str(error)
    if source.get('file_state') == 'modified':
        return 'Archivo modificado: recárguelo antes de generar el reporte.'
    if source.get('file_state') == 'unavailable':
        return 'Archivo no disponible: restáurelo o seleccione su ubicación actual y recárguelo.'
    return None
