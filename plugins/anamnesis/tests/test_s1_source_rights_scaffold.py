"""Keep the source-rights specification reproducible outside a Fiat run."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / 'plugins/anamnesis/docs/source-rights'
RESOLVER = DOCS / 'reports/resolve.py'
PINS = {
    'study.md': '9d1e4649ca7a322ac5ec76d9b1fed585ed4daedbdced3c89f79671def5d09a03',
    'runbook.md': '1b71d01facea6835e3d888617acbcb2c6e130304cf41bd43dd87e43cde8b34ce',
    'design-evidence.json': '80b1946d5db7c7133c4a8c377d80df36ecb8c8b1b7cb6fda0f04b56975a9d574',
}


def scratch_directory():
    scratch = ROOT / 'tmp'
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix='anamnesis-source-rights-')


class SourceRightsScaffoldTests(unittest.TestCase):
    def load_resolver(self):
        self.assertTrue(RESOLVER.is_file(), 'the committed resolver is absent')
        spec = importlib.util.spec_from_file_location('source_rights_resolver', RESOLVER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def design(self):
        path = DOCS / 'design-evidence.json'
        self.assertTrue(path.is_file(), 'the committed design record is absent')
        return json.loads(path.read_bytes())

    def test_receipted_document_bytes_survive_commit(self):
        for name, digest in PINS.items():
            with self.subTest(name=name):
                path = DOCS / name
                self.assertTrue(path.is_file(), name)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_selection_matrix_and_report_digests_are_complete(self):
        design = self.design()
        candidates = {'manifest-only', 'full-rights', 'retained-rights'}
        criteria = {'rights-bound', 'private-prose', 'row-bytes', 'probe-ms',
                    'ids-moved', 'repeatable', 'implementation'}
        self.assertEqual({item['id'] for item in design['candidates']}, candidates)
        self.assertEqual({item['id'] for item in design['criteria']}, criteria)
        cells = design['results']
        self.assertEqual(len(cells), 21)
        self.assertEqual({(item['candidate'], item['criterion']) for item in cells},
                         {(candidate, criterion) for candidate in candidates for criterion in criteria})
        self.assertEqual(design['selection']['candidate'], 'retained-rights')
        retained = []
        for cell in cells:
            if cell['criterion'] == 'implementation':
                self.assertEqual(cell['state'], 'pending')
                continue
            report = cell['report']
            path = DOCS / report['path']
            self.assertTrue(path.is_file(), str(path))
            body = path.read_bytes()
            self.assertEqual(hashlib.sha256(body).hexdigest(), report['sha256'])
            value = json.loads(body)
            self.assertEqual((value['candidate'], value['criterion']),
                             (cell['candidate'], cell['criterion']))
            self.assertEqual(value['exit'], 0)
            retained.append(path.name)
        reports = {path.name for path in (DOCS / 'reports').glob('*.json')}
        self.assertEqual(reports - {'retained-rights-implementation.json'}, set(retained))
        self.assertEqual(len(retained), 18)

    def test_selected_construction_retains_only_decision_digest(self):
        resolver = self.load_resolver()
        source = {'id': 'probe', 'sha256': 'a' * 64, 'bytes': 1,
                  'rights': {'basis': 'contract', 'disclosure': 'public',
                             'holder': 'private holder', 'statement': 'private statement'}}
        row = resolver.row('retained-rights', source)
        self.assertEqual(set(row), {'id', 'sha256', 'bytes', 'disclosure', 'basis', 'rights_sha256'})
        self.assertEqual(row['rights_sha256'], hashlib.sha256(resolver.canonical(source['rights'])).hexdigest())
        self.assertNotIn('private holder', json.dumps(row))
        self.assertNotIn('private statement', json.dumps(row))

    def test_resolver_runs_from_an_unrelated_directory_with_fresh_output(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            resolver = self.load_resolver()
            self.assertEqual(resolver.ROOT, ROOT, 'resolver inputs must not depend on the caller directory')
            target = Path(directory) / 'fresh.json'
            with mock.patch('sys.argv', [str(RESOLVER), 'retained-rights', 'rights-bound', '--out', str(target)]), contextlib.redirect_stdout(io.StringIO()):
                resolver.main()
            report = json.loads(target.read_bytes())
            self.assertEqual((report['value'], report['unit']), (12, 'count'))
            self.assertEqual(report['candidate'], 'retained-rights')

    def test_resolver_refuses_to_overwrite_a_report(self):
        resolver = self.load_resolver()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'existing.json'
            target.write_bytes(b'protected report\n')
            with mock.patch('sys.argv', [str(RESOLVER), 'retained-rights', 'rights-bound', '--out', str(target)]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises((FileExistsError, SystemExit)):
                    resolver.main()
            self.assertEqual(target.read_bytes(), b'protected report\n')

    def test_resolver_bounds_inputs_and_refuses_symlink_files(self):
        resolver = self.load_resolver()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'input.json'
            target.write_bytes(b' ' * (resolver.MAX_INPUT_BYTES + 1))
            with self.assertRaises(ValueError):
                resolver.read_json(target)
            target.write_text('{}')
            alias = Path(directory) / 'alias.json'
            alias.symlink_to(target)
            with self.assertRaises(OSError):
                resolver.read_json(alias)

    def test_existing_step_reporter_interface_remains_available(self):
        reporter_path = ROOT / 'plugins/anamnesis/tests/elenchus.py'
        spec = importlib.util.spec_from_file_location('source_rights_reporter', reporter_path)
        reporter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reporter)
        with scratch_directory() as directory:
            step, target = reporter.parse(['--step', '1', str(Path(directory) / 'result.json')])
            self.assertEqual(step, 1)
            self.assertEqual(target[0], ROOT)
            self.assertEqual(target[2][-1], 'result.json')

    def test_decision_has_one_existing_ledger_home(self):
        study = DOCS / 'study.md'
        self.assertTrue(study.is_file(), 'the committed study is absent')
        self.assertIn('record | plugins/anamnesis/skills/anamnesis/EVOLUTION.md', study.read_text())
        ledger = (ROOT / 'plugins/anamnesis/skills/anamnesis/EVOLUTION.md').read_text()
        for candidate in ('retained-rights', 'manifest-only', 'full-rights'):
            self.assertIn(candidate, ledger)

    def test_audit_reading_evidence_is_retained(self):
        path = DOCS / 'audit-read-evidence.json'
        self.assertTrue(path.is_file())
        evidence = json.loads(path.read_bytes())
        self.assertEqual(evidence['base'], '7952eafa337f5ba1c4f45417ceb154673f629c1c')
        self.assertEqual(evidence['whole_set_exit'], 0)
        self.assertEqual(len(evidence['sources']), 4)
        for source in evidence['sources']:
            for key in ('source', 'view'):
                self.assertEqual(hashlib.sha256((ROOT / source[key]).read_bytes()).hexdigest(), source[key + '_sha256'])


if __name__ == '__main__':
    unittest.main()
