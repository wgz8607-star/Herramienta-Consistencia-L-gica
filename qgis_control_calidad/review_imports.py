"""Track detail imports independently and reversibly within the current run."""
from copy import deepcopy
from dataclasses import replace

from .review import REVIEW_FIELDS, restore_review
from .report_exceptions import FIELDS as EXCEPTION_FIELDS

TRACKING_FIELDS = REVIEW_FIELDS + EXCEPTION_FIELDS


def tracking(case):
    return tuple(getattr(case, name) for name in TRACKING_FIELDS)


def assign(case, values):
    for name, value in zip(TRACKING_FIELDS, values):
        setattr(case, name, value)


class ReviewImports:
    def __init__(self, cases):
        self.cases = cases
        self.sources = {}

    def snapshot(self):
        return deepcopy(self.sources)

    def restore_snapshot(self, snapshot):
        self.sources = deepcopy(snapshot)

    def _release(self, component, cases):
        source = self.sources.get(component)
        counts = {'retiradas': 0, 'conservadas': 0}
        for index, (before, after) in (source or {}).get('changes', {}).items():
            if tracking(cases[index]) == after:
                assign(cases[index], before)
                counts['retiradas'] += 1
            else:
                counts['conservadas'] += 1
        return counts

    def release(self, component):
        counts = self._release(component, self.cases)
        self.sources.pop(component, None)
        return counts

    def load(self, component, path, records):
        if not any(case.component == component for case in self.cases):
            raise ValueError('No hay resultados de este detalle en la ejecución actual.')
        declared = {record.component for record in records if record.component}
        if declared and declared != {component}:
            raise ValueError(f'El archivo contiene {", ".join(sorted(declared))}; seleccione el detalle {component}.')
        current_keys = {case.key for case in self.cases if case.component == component}
        if not declared and records and not any(record.key in current_keys for record in records):
            raise ValueError('El archivo no identifica el componente y no tiene coincidencias con este detalle.')
        # Stage replacements so an error does not destroy a previous successful import.
        candidate = [replace(case) for case in self.cases]
        released = self._release(component, candidate)
        before = {index: tracking(case) for index, case in enumerate(candidate) if case.component == component}
        scoped = [case for case in candidate if case.component == component]
        counts = restore_review(scoped, records)
        counts['coincidencias'] = sum(record.key in current_keys and record.valid for record in records)
        counts['ediciones_conservadas'] = released['conservadas']
        changes = {index: (values, tracking(candidate[index])) for index, values in before.items()
                   if values != tracking(candidate[index])}
        for index in before:
            assign(self.cases[index], tracking(candidate[index]))
        self.sources[component] = {'path': str(path), 'counts': dict(counts), 'changes': changes}
        return counts
