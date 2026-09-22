"""Runbook-owned local interfaces retain exact source and receipt custody."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'plugins/hexaemeron/skills/protasis/scripts/gate_commands.py'
spec = importlib.util.spec_from_file_location('registered_gate_tests', SOURCE)
gates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)
CLI = 'scripts/verify.py'
RELEASED_ADAPTERS = (
    '00d4c9f2a0905ea65d56a3ddca9a429c9a20d464d9b66f69098a954b5e7c37b0',
    '18eb52e7e6bc741bd2c80c55838de74831777ea0833147570963c10e0904c093',
    'c2d14b0f262ecde17f679a73a462cd2ed0f4305a54528e93e375f2b36514bbc6',
)
PROGRAM = '''import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--count', type=int, choices=[1, 2], default=1)
    parser.add_argument('--report')
    args = parser.parse_args()
    return args
'''


class RunbookRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.path = self.root / CLI
        self.path.parent.mkdir()
        self.path.write_text(PROGRAM)

    def fence(self, rows=None):
        if rows is None:
            rows = CLI + ' | main | ' + gates.digest(self.path.read_bytes())
        return '```command-interfaces\nschema | protasis-command-interfaces/v1\n' + rows + '\n```\n'

    def book(self, suffix='', fence=None):
        return ((self.fence() if fence is None else fence) + '\n## Step 1: Verify\n\n'
                '**Exit.** `python3 ' + CLI + ' --root . ' + suffix + '`\n').encode()

    def test_declared_source_accepts_real_arguments_without_execution(self):
        marker = self.root / 'executed'
        self.path.write_text(PROGRAM + '\nPath(' + repr(str(marker)) + ').touch()\n')
        data = self.book('--count 2')
        receipt = gates.validate(self.root, data)
        self.assertFalse(marker.exists())
        self.assertFalse(receipt['operation_ran'])
        self.assertEqual(receipt['commands'][0]['invocations'][0]['cli']['sha256'],
                         gates.digest(self.path.read_bytes()))
        gates.replay(self.root, data, receipt)

    def test_arguments_and_missing_registration_still_refuse(self):
        for suffix in ('--count 3', '--count nope', '--unknown', '--report a b'):
            with self.subTest(suffix=suffix), self.assertRaises(gates.Refusal):
                gates.validate(self.root, self.book(suffix))
        with self.assertRaisesRegex(gates.Refusal, 'unregistered-cli'):
            gates.validate(self.root, self.book(fence=''))

    def test_changed_source_cannot_reuse_registration_or_receipt(self):
        data = self.book()
        receipt = gates.validate(self.root, data)
        self.path.write_text(PROGRAM + '\n# changed source\n')
        with self.assertRaisesRegex(gates.Refusal, 'registered-source-drift'):
            gates.validate(self.root, data)
        with self.assertRaises(gates.Refusal):
            gates.replay(self.root, self.book(), receipt)

    def test_released_adapter_replays_unchanged_local_interface_without_rewriting(self):
        marker = self.root / 'executed'
        self.path.write_text(PROGRAM + '\nPath(' + repr(str(marker)) + ').touch()\n')
        data = self.book('--count 2')
        current = gates.validate(self.root, data)
        self.assertEqual(current['adapter_sha256'], gates.digest(SOURCE.read_bytes()))
        for adapter in RELEASED_ADAPTERS:
            receipt = copy.deepcopy(current)
            receipt['adapter_sha256'] = adapter
            before = copy.deepcopy(receipt)
            with self.subTest(adapter=adapter):
                gates.replay(self.root, data, receipt)
                self.assertEqual(receipt, before)
                self.assertFalse(marker.exists())
                self.assertFalse(receipt['operation_ran'])

    def test_released_adapter_still_refuses_source_and_receipt_drift(self):
        data = self.book('--count 2')
        current = gates.validate(self.root, data)
        for adapter in RELEASED_ADAPTERS:
            receipt = copy.deepcopy(current)
            receipt['adapter_sha256'] = adapter
            for field, value in (('artifact_sha256', '0' * 64), ('operation_ran', True)):
                altered = copy.deepcopy(receipt)
                altered[field] = value
                with self.subTest(adapter=adapter, field=field), self.assertRaises(gates.Refusal):
                    gates.replay(self.root, data, altered)
            altered = copy.deepcopy(receipt)
            altered['commands'][0]['invocations'][0]['argv'][-1] = '1'
            with self.subTest(adapter=adapter, field='argv'), self.assertRaises(gates.Refusal):
                gates.replay(self.root, data, altered)
            self.path.write_text(PROGRAM + '\n# changed source\n')
            with self.subTest(adapter=adapter, field='source'), self.assertRaisesRegex(gates.Refusal, 'registered-source-drift'):
                gates.replay(self.root, data, receipt)
            self.path.write_text(PROGRAM)

    def test_unknown_and_malformed_adapter_identities_refuse(self):
        data = self.book()
        for adapter in ('0' * 64, '', None, [], {}):
            receipt = gates.validate(self.root, data)
            receipt['adapter_sha256'] = adapter
            with self.subTest(adapter=adapter), self.assertRaises(gates.Refusal):
                gates.replay(self.root, data, receipt)

    def test_append_only_registration_replacement_and_retirement(self):
        data = self.book()
        receipt = gates.validate(self.root, data)
        self.path.write_text(PROGRAM + '\n# reviewed amendment\n')
        replacement = ('\n### Amendment -- 2026-09-16\n\n' + self.fence()).encode()
        revised = data + replacement
        current = gates.validate(self.root, revised)
        self.assertEqual(revised[:len(data)], data)
        self.assertEqual(receipt['artifact_sha256'], gates.digest(data))
        gates.replay(self.root, revised, current)
        retired = data + ('\n### Amendment -- 2026-09-16\n\n' + self.fence('')).encode()
        with self.assertRaisesRegex(gates.Refusal, 'unregistered-cli'):
            gates.validate(self.root, retired)

    def test_duplicate_misplaced_and_malformed_declarations_refuse(self):
        row = CLI + ' | main | ' + gates.digest(self.path.read_bytes())
        bad = [self.fence(row + '\n' + row), self.fence() + self.fence(),
               self.fence().replace('v1', 'v2'), self.fence().replace('main |', 'bad-name |'),
               self.fence().replace(gates.digest(self.path.read_bytes()), '0' * 63)]
        for fence in bad:
            with self.subTest(fence=fence), self.assertRaises(gates.Refusal):
                gates.validate(self.root, self.book(fence=fence))
        with self.assertRaises(gates.Refusal):
            gates.validate(self.root, self.book(fence='') + self.fence().encode())
        with self.assertRaises(gates.Refusal):
            gates.validate(self.root, self.book() + ('\n### Amendment -- invalid\n' + self.fence()).encode())

    def test_unsafe_paths_registry_shadow_and_count_refuse(self):
        sha = gates.digest(self.path.read_bytes())
        for path in ('../x.py', '/x.py', 'scripts/../x.py', '.git/x.py',
                     'scripts\\x.py', 'scripts//x.py', 'x.sh', next(iter(gates.REGISTRY)),
                     next(iter(gates.REGISTRY)).upper().replace('.PY', '.py')):
            with self.subTest(path=path), self.assertRaises(gates.Refusal):
                gates.validate(self.root, self.book(fence=self.fence(path + ' | main | ' + sha)))
        rows = '\n'.join('scripts/x' + str(i) + '.py | main | ' + sha for i in range(33))
        with self.assertRaises(gates.Refusal):
            gates.validate(self.root, self.book(fence=self.fence(rows)))

    def test_unused_declarations_are_checked_and_symlinks_refuse(self):
        row = 'scripts/absent.py | main | ' + '0' * 64
        with self.assertRaises(gates.Refusal):
            gates.validate(self.root, self.book(fence=self.fence().replace('\n```', '\n' + row + '\n```')))
        data = self.book()
        actual = self.root / 'actual.py'
        self.path.rename(actual)
        self.path.symlink_to(actual)
        with self.assertRaises(gates.Refusal):
            gates.validate(self.root, data)

    def test_dynamic_parser_and_unknown_converter_refuse_even_when_pinned(self):
        for candidate in (PROGRAM.replace('type=Path', 'type=custom'),
                          PROGRAM.replace('    parser.add_argument', '    if True:\n        parser.add_argument', 1),
                          PROGRAM.replace('args = parser.parse_args()', 'args = parser.parse_args(["--root", "fake"])')):
            self.path.write_text(candidate)
            with self.subTest(candidate=candidate), self.assertRaises(gates.Refusal):
                gates.validate(self.root, self.book())

    def test_report_binding_relocation_and_forgery(self):
        data = (self.fence() + '\n## Step 1: Verify\n\n'
                '**Tests.** Elenchus command: `python3 ' + CLI +
                ' --root . --report {report}`; format: `unittest-json-v1`; '
                'report file: `.hexaemeron/reports/result.json`.\n').encode()
        receipt = gates.validate(self.root, data)
        with tempfile.TemporaryDirectory() as other:
            other = Path(other).resolve()
            (other / CLI).parent.mkdir()
            (other / CLI).write_bytes(self.path.read_bytes())
            for adapter in (receipt['adapter_sha256'], *RELEASED_ADAPTERS):
                historical = copy.deepcopy(receipt)
                historical['adapter_sha256'] = adapter
                with self.subTest(adapter=adapter):
                    gates.replay(other, data, historical)
                    altered = copy.deepcopy(historical)
                    altered['commands'][0]['invocations'][0]['execution_argv'][-1] = str(other / '.hexaemeron/reports/result.json')
                    with self.assertRaises(gates.Refusal):
                        gates.replay(other, data, altered)
            (other / '.hexaemeron').mkdir(exist_ok=True)
            (other / '.hexaemeron/reports').symlink_to(self.root, target_is_directory=True)
            with self.assertRaises(gates.Refusal):
                gates.replay(other, data, historical)
        altered = copy.deepcopy(receipt)
        altered['commands'][0]['invocations'][0]['cli']['sha256'] = '0' * 64
        with self.assertRaises(gates.Refusal):
            gates.replay(self.root, data, altered)


try:
    from .hexctl_harness import HexctlCase
except ImportError:
    from hexctl_harness import HexctlCase


class RegisteredReceiptTests(HexctlCase):
    def test_real_receipt_refuses_drift_and_accepts_preserved_amendment(self):
        import json
        self.run_ctl('init', '--topic', 'Registered target CLI')
        self.write_design_evidence()
        self.write(CLI, PROGRAM)
        study = self.write('study.md', '# Study\n\n```risk-register\nsource | drift | replay\n```\n')
        self.run_ctl('done', 'study', '--artifact', study, '--skills', 'hexaemeron:protasis')
        def fence():
            sha = gates.digest(Path(self.target, CLI).read_bytes())
            return ('```command-interfaces\nschema | protasis-command-interfaces/v1\n' +
                    CLI + ' | main | ' + sha + '\n```\n')
        command = 'python3 ' + CLI + ' --root .'
        text = ('# Runbook\n\n' + fence() + '\n## Step 1: Gate\n\n'
                '**Goal.** Validate.\n**Entry.** Source.\n**Exit.** `' + command + '`\n'
                '**Files.** ' + CLI + '\n**Tests.** Interface tests.\n'
                '**Disciplines.** phylax: parse without imports.\n')
        runbook = self.write('runbook.md', text)
        steps = self.write('steps.json', json.dumps(['Gate']))
        self.run_ctl('done', 'runbook', '--artifact', runbook, '--steps-file', steps)
        self.run_ctl('verify')
        text = Path(self.target, runbook).read_text()
        original = copy.deepcopy(self.state()['receipts']['runbook']['gate_commands'])
        self.write(CLI, PROGRAM + '\n# approved source revision\n')
        self.run_ctl('verify', expect=1)
        before = Path(self.target, '.hexaemeron/state.json').read_bytes()
        self.run_ctl('config', 'set', 'audit.max_rounds', '7', expect=1)
        self.assertEqual(Path(self.target, '.hexaemeron/state.json').read_bytes(), before)
        amendment = self.runbook_amendment(
            verdicts='Step 1: entry holds; exit holds.', touched='Step 1.',
            what='Complete replacement Exit: Run `' + command + '`.\n\n' + fence())
        candidate = self.write('candidate.md', text + amendment)
        self.run_ctl('amend', 'runbook', '--artifact', candidate)
        self.run_ctl('verify')
        receipt = self.state()['receipts']['runbook']
        self.assertEqual(receipt['gate_commands'], original)
        self.assertEqual(Path(self.target, runbook).read_bytes()[:len(text.encode())], text.encode())
        self.assertEqual(len(receipt['amendments']), 1)


if __name__ == '__main__':
    unittest.main()
