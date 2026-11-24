"""Independent QGIS plugin for R1 numbering maxima."""
def classFactory(iface):
    from .plugin import MaximaPlugin
    return MaximaPlugin(iface)
