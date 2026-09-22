"""Only the reviewed report-timestamp source pair may replay old runner receipts."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'plugins/hexaemeron/skills/protasis/scripts/gate_commands.py'
spec = importlib.util.spec_from_file_location('runner_compatibility_gate', SOURCE)
gates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)
RUNNER = 'plugins/hexaemeron/tests/run_tests.py'
OLD_ADAPTER = 'eacd55c44ff05a8a8899143066795bdb1a02fd869c9f4ec12cca55a20252b279'
OLD_RUNNER = 'ac11ed0c2a403e509badf8f78a7583062965691c4ea28d9518148d7a50c54e4b'
NEW_RUNNER = 'c8e63d2c2f0d595172d6be22f387da66a8b4bbb0b0d3f8404f772519b504deb8'


class RunnerCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.runner = self.root / RUNNER
        self.runner.parent.mkdir(parents=True)
        self.runner.write_bytes((ROOT / RUNNER).read_bytes())
        self.book = ''.join(
            f'**Tests.** Elenchus command: `python3 {RUNNER} --jobs 12 '
            '--elenchus-report {report}`; format: `unittest-json-v1`; '
            f'report file: `.elenchus/step-{n}.json`.\n'
            for n in range(1, 6)
        ).encode()

    def historical(self):
        receipt = gates.validate(self.root, self.book)
        receipt['adapter_sha256'] = OLD_ADAPTER
        for command in receipt['commands']:
            for invocation in command['invocations']:
                if invocation['cli']['path'] == RUNNER:
                    invocation['cli']['sha256'] = OLD_RUNNER
        return receipt

    def test_exact_pair_replays_without_rewriting_or_claiming_execution(self):
        receipt = self.historical()
        before = copy.deepcopy(receipt)
        gates.replay(self.root, self.book, receipt)
        self.assertEqual(receipt, before)
        self.assertFalse(receipt['operation_ran'])
        fresh = gates.validate(self.root, self.book)
        self.assertEqual(fresh['commands'][0]['invocations'][0]['cli']['sha256'], NEW_RUNNER)

    def test_reviewed_source_delta_is_only_descriptor_timestamp_repair(self):
        source = self.runner.read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), NEW_RUNNER)
        additions = (
            '    if os.utime not in getattr(os, "supports_fd", ()):\n'
            '        missing.append("os.utime(fd)")\n',
            '            # Automatic inode timestamps can lag the wall clock on Linux.\n'
            '            # Stamp this completed write through its held descriptor so the\n'
            "            # reader's strict start-time cutoff can remain unchanged.\n"
            '            os.utime(descriptor, ns=(created.st_atime_ns, time.time_ns()))\n',
        )
        for addition in additions:
            self.assertEqual(source.count(addition.encode()), 1)
            source = source.replace(addition.encode(), b'')
        self.assertEqual(hashlib.sha256(source).hexdigest(), OLD_RUNNER)

    def test_unknown_adapter_or_old_runner_digest_refuses(self):
        for kind in ('adapter', 'runner'):
            receipt = self.historical()
            if kind == 'adapter':
                receipt['adapter_sha256'] = '0' * 64
            else:
                receipt['commands'][0]['invocations'][0]['cli']['sha256'] = '0' * 64
            with self.subTest(kind=kind), self.assertRaises(gates.Refusal):
                gates.replay(self.root, self.book, receipt)

    def test_even_comment_only_current_source_drift_refuses(self):
        receipt = self.historical()
        self.runner.write_bytes(self.runner.read_bytes() + b'\n# unreviewed\n')
        with self.assertRaises(gates.Refusal):
            gates.replay(self.root, self.book, receipt)

    def test_declarations_arguments_reports_and_shape_still_refuse(self):
        for kind in ('declaration', 'argv', 'execution', 'report', 'path', 'extra', 'empty', 'malformed'):
            receipt = self.historical()
            invocation = receipt['commands'][0]['invocations'][0]
            if kind == 'declaration': invocation['cli']['declarations_sha256'] = '0' * 64
            elif kind == 'argv': invocation['argv'][3] = '1'
            elif kind == 'execution': invocation['execution_argv'][-1] = '/tmp/other.json'
            elif kind == 'report': receipt['commands'][0]['report']['file'] = '.elenchus/other.json'
            elif kind == 'path': invocation['cli']['path'] = 'other.py'
            elif kind == 'extra': receipt['extra'] = True
            elif kind == 'empty': receipt['commands'] = []
            else: receipt['commands'] = [None]
            with self.subTest(kind=kind), self.assertRaises(gates.Refusal):
                gates.replay(self.root, self.book, receipt)

    def test_current_adapter_cannot_claim_the_historical_runner_digest(self):
        receipt = self.historical()
        receipt['adapter_sha256'] = gates.digest(SOURCE.read_bytes())
        with self.assertRaises(gates.Refusal):
            gates.replay(self.root, self.book, receipt)

    def test_mixed_or_other_invocations_are_outside_the_reviewed_pair(self):
        other = 'plugins/brevitas/skills/brevitas/scripts/brevitas.py'
        path = self.root / other
        path.parent.mkdir(parents=True)
        path.write_bytes((ROOT / other).read_bytes())
        self.book += f'**Exit.** `python3 {other} draft.md`\n'.encode()
        receipt = self.historical()
        with self.assertRaises(gates.Refusal):
            gates.replay(self.root, self.book, receipt)


if __name__ == '__main__':
    unittest.main()
