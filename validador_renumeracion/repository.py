"""Reuse the installed consistency validator configuration without executing it."""
import ast
import json
import importlib.util
from pathlib import Path


LOCAL_CONNECTION_FILE=Path(__file__).with_name('sentencias.local.json')


def repository_params():
    if LOCAL_CONNECTION_FILE.is_file():
        try:
            params=json.loads(LOCAL_CONNECTION_FILE.read_text(encoding='utf-8'))
            valid=isinstance(params,dict) and params.get('dbname')=='sentencias' and all(isinstance(params.get(key),str) and params[key] for key in ('host','port','user','password'))
            if not valid:raise ValueError()
            return {key:params[key] for key in ('host','port','dbname','user','password')}
        except (OSError,ValueError,TypeError):
            raise ValueError('La configuración local de sentencias no es válida. Reinstale el paquete configurado.') from None

    spec=importlib.util.find_spec('qgis_control_calidad')
    if spec is None or not spec.origin:
        raise ValueError('Instale el Validador de Consistencia Lógica para reutilizar su acceso a sentencias.')
    filename=Path(spec.origin).parent/'dialog.py'
    values={}

    class Resolve(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id in values:return ast.Constant(value=values[node.id])
            return node

    for statement in ast.parse(filename.read_text(encoding='utf-8')).body:
        if not isinstance(statement,ast.Assign):continue
        if len(statement.targets)!=1 or not isinstance(statement.targets[0],ast.Name):continue
        name=statement.targets[0].id
        if name not in ('POSTGRES_HOST','REPOSITORY_CONNECTION'):continue
        try:values[name]=ast.literal_eval(Resolve().visit(statement.value))
        except (ValueError,TypeError):continue
    params=values.get('REPOSITORY_CONNECTION')
    if not isinstance(params,dict) or params.get('dbname')!='sentencias' or not params.get('password'):
        raise ValueError('No se encontró una configuración válida de sentencias en el Validador de Consistencia Lógica.')
    return dict(params)
