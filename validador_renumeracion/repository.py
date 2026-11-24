"""Reuse the installed consistency validator configuration without executing it."""
import ast
import json
import importlib.util
from pathlib import Path


LOCAL_CONNECTION_FILE=Path(__file__).with_name('sentencias.local.json')
_SESSION_PASSWORD=None


def repository_params():
    if LOCAL_CONNECTION_FILE.is_file():
        try:
            params=json.loads(LOCAL_CONNECTION_FILE.read_text(encoding='utf-8'))
            valid=isinstance(params,dict) and params.get('dbname')=='sentencias' and all(isinstance(params.get(key),str) and params[key] for key in ('host','port','user','password'))
            if not valid:raise ValueError()
            return {key:params[key] for key in ('host','port','dbname','user','password')}
        except (OSError,ValueError,TypeError):
            raise ValueError('La configuración local de sentencias no es válida. Reinstale el paquete configurado.') from None

    global _SESSION_PASSWORD
    params={'host':'172.19.3.225','port':'5432','dbname':'sentencias','user':'admin_ant'}
    if _SESSION_PASSWORD is None:
        installed=_validator_connection()
        if installed and all(installed.get(key)==value for key,value in params.items()):
            _SESSION_PASSWORD=installed['password']
        else:
            from qgis.PyQt.QtWidgets import QInputDialog,QLineEdit
            password,accepted=QInputDialog.getText(None,'Acceso a sentencias · admin_ant','Contraseña de admin_ant (solo esta sesión):',QLineEdit.Password)
            if not accepted or not password:raise ValueError('Acceso a sentencias cancelado.')
            _SESSION_PASSWORD=password
    return dict(params,password=_SESSION_PASSWORD)


def _validator_connection():
    try:spec=importlib.util.find_spec('qgis_control_calidad')
    except (ImportError,ValueError):return None
    if spec is None or not spec.origin:return None
    filename=Path(spec.origin).parent/'dialog.py'
    values={}

    class Resolve(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id in values:return ast.Constant(value=values[node.id])
            return node

    try:
        statements=ast.parse(filename.read_text(encoding='utf-8')).body
    except (OSError,SyntaxError):return None
    for statement in statements:
        if not isinstance(statement,ast.Assign):continue
        if len(statement.targets)!=1 or not isinstance(statement.targets[0],ast.Name):continue
        name=statement.targets[0].id
        if name not in ('POSTGRES_HOST','REPOSITORY_CONNECTION'):continue
        try:values[name]=ast.literal_eval(Resolve().visit(statement.value))
        except (ValueError,TypeError):continue
    params=values.get('REPOSITORY_CONNECTION')
    return dict(params) if isinstance(params,dict) and params.get('dbname')=='sentencias' and params.get('password') else None
