import sys
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis_control_calidad.review import ImportedReview, build_cases, digest, PENDING
from qgis_control_calidad.review_imports import ReviewImports


def make_cases():
    return build_cases([
        SimpleNamespace(category=c, rule='r1', status='Correcta', criterion_hash=digest(c),
                        identity_safe=True, rows=[{'numero_predial': '00001', 'dato': c}])
        for c in ('Administrativas', 'Juridicas')
    ], {'schema': 'test'})


def record(case, text='Justificado'):
    return ImportedReview(case.key, PENDING, '', '', True, True, ('Sí', text, 'No', ''), case.component)


class ReviewImportTests(unittest.TestCase):
    def setUp(self):
        self.cases = make_cases()
        self.imports = ReviewImports(self.cases)

    def test_separate_dt_operator_missing_notes_and_real_approvals(self):
        result = SimpleNamespace(category='Administrativas', rule='r1', status='Correcta',
                                 criterion_hash=digest('criteria'), identity_safe=True,
                                 rows=[{'numero_predial': str(i).zfill(5), 'dato': 'valor'} for i in range(7)])
        current = build_cases([result], {'schema': 'test'})
        inputs = [
            ('Sí', 'DT directa', 'No', ''),
            ('Sí', '  ', 'No', ''),
            ('No', '', 'Sí', 'Propuesta operador'),
            ('No', '', 'Sí', '  '),
            ('Sí', 'DT aprueba', 'Sí', 'Propuesta justificada'),
            ('Sí', 'DT directa', 'No', 'Solo comentario del operador'),
            ('Sí', 'DT directa', 'Sí', ''),
        ]
        records = [ImportedReview(case.key, PENDING, '', '', True, True, values, case.component)
                   for case, values in zip(current, inputs)]
        manager = ReviewImports(current)
        counts = manager.load('Administrativas', 'detalle.xlsx', records)
        self.assertEqual(counts['dt_incorporadas'], 4)
        self.assertEqual(counts['dt_sin_observacion'], 1)
        self.assertEqual(counts['operador_incorporadas'], 1)
        self.assertEqual(counts['operador_sin_observacion'], 2)
        self.assertEqual(counts['operador_aprobadas_dt'], 1)
        self.assertEqual(counts['operador_bloqueado'], 3)
        self.assertEqual(counts['excepciones_invalidas'], 3)
        self.assertEqual(manager.sources['Administrativas']['counts']['operador_aprobadas_dt'], 1)
        # A recarga is counted again from its file, not accumulated over imports.
        again = manager.load('Administrativas', 'detalle.xlsx', records)
        self.assertEqual(again['dt_incorporadas'], 4)
        self.assertEqual(again['operador_aprobadas_dt'], 1)

    def test_conflicting_proposal_is_not_counted_as_incorporated_or_approved(self):
        current = self.cases[0]
        current.observacion_dt = 'Revisión actual'
        incoming = replace(record(current), exception_values=('Sí', 'DT entrante', 'Sí', 'Propuesta'))
        counts = self.imports.load('Administrativas', 'a.xlsx', [incoming])
        self.assertEqual(counts['conflictos'], 1)
        self.assertEqual(counts['dt_incorporadas'], 0)
        self.assertEqual(counts['operador_aprobadas_dt'], 0)
        self.assertEqual(current.observacion_dt, 'Revisión actual')

    def test_sources_accumulate_and_release_only_one_detail(self):
        self.imports.load('Administrativas', 'a.xlsx', [record(self.cases[0])])
        self.imports.load('Juridicas', 'j.xlsx', [record(self.cases[1])])
        self.assertEqual(len(self.imports.sources), 2)
        counts = self.imports.release('Administrativas')
        self.assertEqual(counts['retiradas'], 1)
        self.assertEqual(self.cases[0].excepcion_dt, 'No')
        self.assertEqual(self.cases[1].excepcion_dt, 'Sí')
        self.assertIn('Juridicas', self.imports.sources)

    def test_reload_replaces_own_previous_revision_even_with_cleared_mark(self):
        old = record(self.cases[0], 'Anterior')
        self.imports.load('Administrativas', 'a.xlsx', [old])
        self.imports.load('Administrativas', 'a.xlsx', [replace(old, exception_values=('No', '', 'Sí', 'Nueva observación'))])
        self.assertEqual(self.cases[0].exception_tracking(), ('No', '', 'Sí', 'Nueva observación'))
        self.imports.load('Administrativas', 'a.xlsx', [replace(old, exception_values=('No', '', 'No', ''))])
        self.assertEqual(self.cases[0].exception_tracking(), ('No', '', 'No', ''))
        self.assertEqual(self.imports.sources['Administrativas']['counts']['conflictos'], 0)

    def test_wrong_component_does_not_destroy_previous_load(self):
        self.imports.load('Administrativas', 'a.xlsx', [record(self.cases[0])])
        with self.assertRaises(ValueError):
            self.imports.load('Administrativas', 'wrong.xlsx', [record(self.cases[1])])
        self.assertEqual(self.cases[0].excepcion_dt, 'Sí')
        self.assertEqual(self.imports.sources['Administrativas']['path'], 'a.xlsx')

    def test_release_and_reload_preserve_edits_not_owned_by_source(self):
        self.imports.load('Administrativas', 'a.xlsx', [record(self.cases[0])])
        self.cases[0].observacion_dt = 'Editada posteriormente'
        counts = self.imports.release('Administrativas')
        self.assertEqual(counts['conservadas'], 1)
        self.assertEqual(self.cases[0].observacion_dt, 'Editada posteriormente')
        counts = self.imports.load('Administrativas', 'a.xlsx', [record(self.cases[0], 'Otra')])
        self.assertEqual(counts['conflictos'], 1)
        self.imports.release('Administrativas')
        self.assertEqual(self.cases[0].observacion_dt, 'Editada posteriormente')

    def test_release_returns_to_preexisting_tracking_not_default(self):
        self.cases[0].observacion_operador = 'Preexistente'
        counts = self.imports.load('Administrativas', 'a.xlsx', [record(self.cases[0])])
        self.assertEqual(counts['conflictos'], 1)
        self.imports.release('Administrativas')
        self.assertEqual(self.cases[0].observacion_operador, 'Preexistente')

    def test_ambiguous_records_are_not_assigned(self):
        rec = record(self.cases[0])
        counts = self.imports.load('Administrativas', 'a.xlsx', [rec, rec])
        self.assertEqual(counts['ambiguas'], 2)
        self.assertEqual(self.cases[0].excepcion_dt, 'No')


if __name__ == '__main__':
    unittest.main()
