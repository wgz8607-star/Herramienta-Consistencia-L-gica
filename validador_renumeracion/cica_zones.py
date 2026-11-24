"""Zone combinations shared by the CICA dashboard and its paginated detail."""
ZONES=('Urbano','Centro poblado','Rural')


def selected_zones(value):
    if value=='':return None
    values=(value,) if isinstance(value,str) else tuple(value)
    if any(zone not in ZONES for zone in values):
        raise ValueError('Selección de zonas CICA no válida.')
    return tuple(zone for zone in ZONES if zone in values)


def zone_matches(zone,code,selection,cp=''):
    zones=selected_zones(selection)
    if zones is None:return True
    return zone in zones and (zone!='Centro poblado' or not cp or code==cp)


def zone_label(selection):
    zones=selected_zones(selection)
    return 'Todas las zonas' if zones is None else ' + '.join(zones) if zones else 'Sin zonas seleccionadas'
