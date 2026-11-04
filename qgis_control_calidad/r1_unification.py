"""One temporary R1 row per complete NPN, keeping the first row read."""
import csv
import hashlib
import json


def unify_r1(reference, progress=None, cancel_check=None):
    if reference.kind != 'R1' or getattr(reference, 'unified', False):
        return reference
    if 'numero_predial' not in reference.columns:
        raise ValueError('R1: falta numero_predial para unificar los registros.')
    npn_index=reference.columns.index('numero_predial')
    path=reference.csv_path.with_name('r1_unificado.csv')
    seen=set();count=duplicates=missing=source_count=total=squares=0
    modulus=1 << 256
    try:
        with reference.csv_path.open(encoding='utf-8',newline='') as source,path.open('w',encoding='utf-8',newline='') as target:
            writer=csv.writer(target,quoting=csv.QUOTE_ALL)
            for values in csv.reader(source):
                source_count+=1
                if source_count % 1000 == 0:
                    if cancel_check:cancel_check()
                    if progress:progress('R1',source_count)
                if len(values)!=len(reference.columns):
                    raise ValueError(f'R1, registro {source_count}: cantidad de columnas incorrecta.')
                npn=values[npn_index].strip()
                if not npn:
                    missing+=1
                    continue
                if npn in seen:
                    duplicates+=1
                    continue
                seen.add(npn)
                values[npn_index]=npn
                writer.writerow(values)
                value=int.from_bytes(hashlib.sha256(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode()).digest(),'big')
                total=(total+value)%modulus;squares=(squares+value*value)%modulus
                count+=1
        if cancel_check:cancel_check()
        reference.fingerprint=hashlib.sha256(json.dumps(('first_npn_v1',reference.columns,count,total,squares)).encode()).hexdigest()
        reference.original_row_count=source_count
        reference.row_count=count
        reference.duplicate_count=duplicates
        reference.missing_npn_count=missing
        reference.csv_path=path
        reference.unified=True
        return reference
    except Exception:
        path.unlink(missing_ok=True)
        raise
