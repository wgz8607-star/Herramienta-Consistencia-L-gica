"""Read QGIS PostgreSQL connections on the main thread; never persist credentials."""
from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsDataSourceUri, QgsProviderRegistry, QgsSettings
try:
    from psycopg2.extensions import parse_dsn
except ImportError:
    parse_dsn = None


def provider_connections():
    provider = QgsProviderRegistry.instance().providerMetadata('postgres')
    return provider.dbConnections() if provider else {}


def connection_names():
    names = set()
    settings = QgsSettings(); settings.beginGroup('PostgreSQL/connections')
    try:
        names.update(settings.childGroups())
    finally:
        settings.endGroup()
    names.update(provider_connections())
    return sorted(names)


def saved_connection_params(name):
    if not name:
        raise ValueError('Seleccione una conexión PostgreSQL guardada en QGIS.')
    if parse_dsn is None:
        raise RuntimeError('El Python de QGIS necesita psycopg2 para usar PostgreSQL.')
    connections = provider_connections()
    if name in connections:
        uri = QgsDataSourceUri(connections[name].uri())
    else:
        settings = QgsSettings(); group = 'PostgreSQL/connections/' + name
        if not settings.contains(group + '/database'):
            raise ValueError('La conexión ya no está disponible. Actualice el listado.')
        uri = QgsDataSourceUri()
        ssl_mode = int(settings.value(group + '/sslmode', 1))
        authcfg = str(settings.value(group + '/authcfg', ''))
        database = str(settings.value(group + '/database', ''))
        user = str(settings.value(group + '/username', ''))
        password = str(settings.value(group + '/password', ''))
        service = str(settings.value(group + '/service', ''))
        if service:
            uri.setConnection(service, database, user, password, QgsDataSourceUri.SslMode(ssl_mode), authcfg)
        else:
            uri.setConnection(str(settings.value(group + '/host', '')), str(settings.value(group + '/port', '5432')),
                              database, user, password, QgsDataSourceUri.SslMode(ssl_mode), authcfg)
    if uri.authConfigId():
        config = QgsAuthMethodConfig()
        if not QgsApplication.authManager().loadAuthenticationConfig(uri.authConfigId(), config, True):
            raise ValueError('No se pudo desbloquear la autenticación de QGIS para esta conexión.')
    try:
        params = parse_dsn(uri.connectionInfo(True))
    except Exception:
        # The URI can contain a password; do not echo parser input or exceptions.
        raise ValueError('No se pudieron obtener los parámetros de la conexión. Revise la autenticación de QGIS o utilice la conexión manual.') from None
    params.pop('authcfg', None)
    if not params.get('dbname') and not params.get('service'):
        raise ValueError('La conexión de QGIS no tiene una base de datos o servicio configurado.')
    return params
