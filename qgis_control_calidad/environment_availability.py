"""Read-only availability check for published, active, nonempty controls."""
from contextlib import closing
import psycopg2
from psycopg2 import sql
from qgis.PyQt.QtWidgets import QComboBox


class EnvironmentSelector(QComboBox):
    before_open = None

    def showPopup(self):
        if self.before_open:
            self.before_open()
        super().showPopup()


def has_active_controls(params, source):
    if source is None:
        return False
    with closing(psycopg2.connect(**params, connect_timeout=8)) as connection:
        connection.set_session(readonly=True)
        with connection, connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='15s'")
            if source['kind']=='tables':
                for table in source['tables']:
                    cursor.execute(sql.SQL("SELECT EXISTS (SELECT 1 FROM {}.{} r WHERE r.activa AND r.tipo='CONTROL' AND COALESCE(r.sentencia_sql,'') ~ '[^[:space:]]' AND (SELECT v.version_publicada FROM {}.{} v WHERE v.version=r.version ORDER BY v.orden NULLS LAST,v.componente,v.codigo_regla LIMIT 1) IS TRUE)").format(sql.Identifier(source['schema']),sql.Identifier(table),sql.Identifier(source['schema']),sql.Identifier(table)))
                    if cursor.fetchone()[0]:return True
                return False
            cursor.execute(sql.SQL("SELECT EXISTS (SELECT 1 FROM {}.reglas r JOIN {}.versiones v ON v.id=r.version_id WHERE v.estado='PUBLICADA' AND r.activa AND r.tipo='CONTROL' AND COALESCE(r.sentencia_sql,'') ~ '[^[:space:]]')").format(sql.Identifier(source['schema']),sql.Identifier(source['schema'])))
            return bool(cursor.fetchone()[0])
