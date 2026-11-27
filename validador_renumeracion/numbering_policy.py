"""Shared provisional policy used by identification and every recalculation."""
def normalize_cica_prefixes(value='789'):
    values=set(value)
    if values-set('789'):raise ValueError('Solo se admiten 7xxx, 8xxx y 9xxx como series CICA.')
    return ''.join(c for c in '789' if c in values or c=='9')


def is_provisional(value,model,cica_prefixes='789'):
    return value in cica_prefixes if model=='CICA' else value.isascii() and value.isalpha()
