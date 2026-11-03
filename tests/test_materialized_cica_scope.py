"""Compare the old views and materialized session scopes with actual SQL rows."""
from collections import Counter
import re
import sqlite3
import unittest
from unittest.mock import patch
from psycopg2 import sql
from qgis_control_calidad.territorial_scope import install_scope
from test_cica_source_selection import render


class ScopeDatabase:
    def __init__(self):
        self.db = sqlite3.connect(':memory:')
        self.db.create_function('btrim', 1, lambda value: value.strip() if value is not None else None)
        self.db.create_function('regexp', 2, lambda pattern, value: bool(re.search(pattern, value or '')))
        self.rows = []; self.statements = []
        self.db.execute('CREATE TABLE cica_predio (numero_predial TEXT, etapa TEXT)')
        self.db.executemany('INSERT INTO cica_predio VALUES (?,?)',[
            ('084210100000100001000000000001','ASIGNADO'),
            ('084210100000100001000000000001','ASIGNADO'),
            ('084210000000100001000000000002','TRAMITADO'),
            ('084210200000100001000000000003',None),
            ('130060100000100001000000000004','ASIGNADO'),
            (None,'ASIGNADO'),('','ASIGNADO')])
        for table in ('cica_contacto','cica_seguimiento_control','cica_terreno','reference_r1','reference_r2'):
            self.db.execute(f'CREATE TABLE {table} (numero_predial TEXT, dato TEXT)')
            self.db.executemany(f'INSERT INTO {table} VALUES (?,?)',[
                ('084210100000100001000000000001','duplicado'),
                ('084210100000100001000000000001','duplicado'),
                (' 084210100000100001000000000001 ','espacios'),
                ('084210000000100001000000000002',None),
                ('084210200000100001000000000003','MULTIPOLYGON (((0 0,1 0,1 1,0 0)))'),
                ('084210100000100001000000000099','sin predio'),
                ('130060100000100001000000000004','otro municipio'),
                (None,'sin NPN'),('','vacío')])
    def cursor(self): return self
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def execute(self,statement,params=()):
        query=render(statement);self.statements.append(query)
        if 'information_schema.columns' in query:
            self.rows=[]
        elif 'pg_attribute' in query:
            table=params[0].split('.')[-1].strip('"')
            self.rows=[(row[1],) for row in self.db.execute(f'PRAGMA main.table_info("{table}")')]
        else:
            query=query.replace('ON COMMIT PRESERVE ROWS','').replace('::text','').replace(' ~ ',' REGEXP ')
            query=query.replace('"pg_temp".','main.')
            self.db.execute(query)
            self.rows=[]
    def fetchall(self):return self.rows


class MaterializedCicaScopeTests(unittest.TestCase):
    def test_filtered_rows_match_views_including_duplicates_nulls_and_r1_r2(self):
        for scope,prefixes,selection in [
            ('all',(),{'municipality':'08421','stages':('ASIGNADO',)}),
            ('urban',(),{'municipality':'08421','stages':('ASIGNADO','TRAMITADO')}),
            ('urban+rural',('08421010000010000',),{'municipality':'08421','stages':('ASIGNADO',)}),
            ('center',(),{'municipality':'08421','stages':('',)}),
            ('all',(),{'municipality':'','stages':('ASIGNADO','TRAMITADO','')}),
            ('all',(),{'municipality':'99999','stages':('ASIGNADO',)}),
        ]:
            outputs=[]
            for materialize in (False,True):
                db=ScopeDatabase()
                try:
                    with patch.object(sql.Identifier,'as_string',lambda self,conn:render(self)):
                        mapping=install_scope(db,'pg_temp',{'cica_predio','cica_contacto','cica_seguimiento_control','cica_terreno'},['reference_r1','reference_r2'],scope,prefixes,cica_filter=selection,materialize=materialize)
                    outputs.append({key:Counter(db.db.execute(f'SELECT * FROM temp."{name}"').fetchall()) for key,name in mapping.items()})
                    creates=[q for q in db.statements if q.startswith('CREATE')]
                    self.assertTrue(creates)
                    self.assertTrue(all(q.startswith('CREATE TEMP TABLE' if materialize else 'CREATE TEMP VIEW') for q in creates))
                    if materialize:
                        for name in mapping.values():
                            self.assertEqual(db.db.execute('SELECT type FROM sqlite_temp_master WHERE name=?',(name,)).fetchone()[0],'table')
                    self.assertFalse(any(q.startswith(('UPDATE','DELETE','INSERT','DROP')) for q in db.statements))
                finally:db.db.close()
            self.assertEqual(outputs[0],outputs[1],(scope,prefixes,selection))
            if scope=='all' and selection['municipality']=='08421' and selection['stages']==('ASIGNADO',):
                self.assertEqual(sum(outputs[1][('pg_temp','cica_predio')].values()),2)
                self.assertEqual(sum(outputs[1][('pg_temp','cica_contacto')].values()),3)
                self.assertGreater(sum(outputs[1][('pg_temp','reference_r1')].values()),3)
