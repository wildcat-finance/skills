"""Inert interface and exact receipt regression specimens."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'plugins/hexaemeron/skills/protasis/scripts/gate_commands.py'
spec = importlib.util.spec_from_file_location('gate_commands_tests', SOURCE)
gates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)
BREVITAS = 'plugins/brevitas/skills/brevitas/scripts/brevitas.py'
COMMAND = 'python3 ' + BREVITAS + ' one.md'


class GateCommandTests(unittest.TestCase):
    def test_report_receipt_relocation_preserves_original_derivation(self):
        runner = 'plugins/hexaemeron/tests/run_tests.py'
        data = ('**Tests.** Elenchus command: `python3 ' + runner +
                ' --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; '
                'report file: `.hexaemeron/reports/result.json`.\n').encode()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            roots = [Path(first), Path(second)]
            for root in roots:
                path = root / runner
                path.parent.mkdir(parents=True)
                path.write_bytes((ROOT / runner).read_bytes())
            receipt = gates.validate(roots[0], data)
            before = copy.deepcopy(receipt)
            gates.replay(roots[1], data, receipt)
            self.assertEqual(receipt, before)
            self.assertEqual(receipt['source_root'], str(roots[0].resolve()))
            for field in ('source_root', 'execution_argv'):
                forged = copy.deepcopy(receipt)
                if field == 'source_root':
                    forged[field] = str(roots[1].resolve())
                else:
                    forged['commands'][0]['invocations'][0][field][-1] = str(roots[1] / '.hexaemeron/reports/result.json')
                with self.subTest(field=field), self.assertRaises(gates.Refusal):
                    gates.replay(roots[1], data, forged)
            (roots[1] / '.hexaemeron').symlink_to(roots[0], target_is_directory=True)
            with self.assertRaises(gates.Refusal):
                gates.replay(roots[1], data, receipt)

    def test_nargs_bound_precedes_argparse_allocation(self):
        from unittest import mock
        original = (ROOT / BREVITAS).read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / BREVITAS
            path.parent.mkdir(parents=True)
            for value in ('1000000000', '-1', 'True', '1.5'):
                source = original
                marker = '    return parser'
                self.assertIn(marker, source)
                path.write_text(source.replace(marker, '    parser.add_argument("--arity-probe", nargs=' + value + ')\n' + marker, 1))
                def observed(parser, *args, **kwargs):
                    if args == ('--arity-probe',):
                        self.fail('unsupported nargs reached argparse')
                    return actual(parser, *args, **kwargs)
                actual = gates.InertParser.add_argument
                with self.subTest(nargs=value), mock.patch.object(gates.InertParser, 'add_argument', observed):
                    with self.assertRaises(gates.Refusal):
                        gates.interface(root, BREVITAS)

    def test_bounded_nargs_preserves_argparse_action_semantics(self):
        original = (ROOT / BREVITAS).read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / BREVITAS
            path.parent.mkdir(parents=True)
            for value in ('1', '128', 'None', '"?"', '"*"', '"+"'):
                path.write_text(original.replace('    return parser', '    parser.add_argument("--arity-probe", nargs=' + value + ')\n    return parser', 1))
                with self.subTest(nargs=value):
                    parser, _ = gates.interface(root, BREVITAS)
                    parser.parse_args(['draft.md'])
            path.write_text(original.replace('    return parser', '    parser.add_argument("--arity-probe", nargs=0)\n    return parser', 1))
            with self.assertRaisesRegex(gates.Refusal, 'unsupported-cli-argument-declaration'):
                gates.interface(root, BREVITAS)
            # Ordinary flag actions retain their own zero-operand behavior.
            path.write_text(original.replace('    return parser', '    parser.add_argument("--arity-probe", action="store_true")\n    return parser', 1))
            parser, _ = gates.interface(root, BREVITAS)
            self.assertTrue(parser.parse_args(['draft.md', '--arity-probe']).arity_probe)

    def test_actual_brevitas_arity_and_choices(self):
        gates.validate_command(ROOT, COMMAND)
        for suffix in (' two.md three.md four.md', ' --mode unknown', ' --s one.md'):
            with self.subTest(suffix=suffix), self.assertRaises(gates.Refusal):
                gates.validate_command(ROOT, COMMAND + suffix)

    def test_shell_comment_tilde_and_literal_argv_substitution_refuse(self):
        for suffix in (' # ignored', ' ~/draft.md', ' "#literal"', ' "~literal"'):
            with self.subTest(suffix=suffix), self.assertRaises(gates.Refusal):
                gates.validate_command(ROOT, COMMAND + suffix)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'plugins/hexaemeron/skills/protasis/scripts/protasis.py'
            path.parent.mkdir(parents=True)
            original = (ROOT / path.relative_to(root)).read_text()
            for operand in ('["fake.md"]', 'unknown()', 'argv, namespace=unknown()'):
                path.write_text(original.replace('parser.parse_args(argv)', 'parser.parse_args(' + operand + ')'))
                with self.subTest(operand=operand), self.assertRaises(gates.Refusal):
                    gates.validate_command(root, 'python3 ' + str(path.relative_to(root)) + ' real.md')

    def test_public_gate_reader_refuses_fifo_and_incompatible_mode(self):
        import os
        import subprocess
        import sys
        command = [sys.executable, str(ROOT / 'plugins/hexaemeron/skills/protasis/scripts/protasis.py')]
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / 'runbook.md'
            os.mkfifo(fifo)
            result = subprocess.run(command + ['--gate-root', str(ROOT), str(fifo)], capture_output=True, timeout=3)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'P008', result.stdout)
            result = subprocess.run(command + ['--study', '--gate-root', str(ROOT), str(fifo)], capture_output=True, timeout=3)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b'applies only to runbooks', result.stderr)

    def test_registered_cli_interfaces_all_have_supported_source(self):
        for path in gates.REGISTRY:
            with self.subTest(path=path):
                gates.interface(ROOT, path)

    def test_registered_runbook_runners(self):
        gates.validate_command(ROOT, 'python3 scripts/run_checks.py --scope hexaemeron')
        result = gates.validate_command(ROOT, 'python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}', {'format': 'unittest-json-v1', 'file': '.hexaemeron/reports/result.json'})
        invocation = result['invocations'][0]
        self.assertEqual(invocation['argv'][-1], '{report}')
        self.assertEqual(invocation['execution_argv'][-1], str(ROOT / '.hexaemeron/reports/result.json'))
        for jobs in ('0', '257', 'no'):
            with self.subTest(jobs=jobs), self.assertRaises(gates.Refusal):
                gates.validate_command(ROOT, 'python3 plugins/hexaemeron/tests/run_tests.py --jobs ' + jobs)

    def test_standalone_injection_fences_remain_executable(self):
        for position in ('before', 'after'):
            bad = b'```sh\npython3 nowhere.py $(touch marker)\n```\n'
            step = ('## Step 1: Run\n\n**Exit.** `' + COMMAND + '`\n').encode()
            source = bad + step if position == 'before' else step + '\n**Files.** none\n'.encode() + bad
            with self.subTest(position=position), self.assertRaises(gates.Refusal):
                gates.validate(ROOT, source)

    def test_finite_loop_quote_binding_and_multiline(self):
        for loop in ('for file in one.md "two drafts.md"; do ' + COMMAND.replace('one.md', '"$file"') + '; done', 'for file in one.md "two drafts.md"\ndo\n' + COMMAND.replace('one.md', '"$file"') + '\ndone'):
            result = gates.validate_command(ROOT, loop)
            self.assertEqual([r['argv'][-1] for r in result['invocations']], ['one.md', 'two drafts.md'])
        with self.assertRaises(gates.Refusal):
            gates.validate_command(ROOT, 'for file in one.md; do ' + COMMAND.replace('one.md', "'\"$file\"'") + '; done')

    def test_no_import_and_exact_cli_source_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / BREVITAS
            path.parent.mkdir(parents=True)
            path.write_bytes((ROOT / BREVITAS).read_bytes())
            source = ('```sh\n' + COMMAND + '\n```\n').encode()
            receipt = gates.validate(root, source)
            gates.replay(root, source, receipt)
            marker = root / 'executed'
            path.write_text(path.read_text() + '\nraise RuntimeError("must not import")\n')
            self.assertFalse(marker.exists())
            with self.assertRaises(gates.Refusal):
                gates.replay(root, source, receipt)

    def test_malformed_fences_and_shells_refuse(self):
        for source in ('```sh\n' + COMMAND, '```unknown\n' + COMMAND + '\n```', '```sh\n' + COMMAND + '\n~~~', '```sh\n' + COMMAND + ' && touch marker\n```'):
            with self.subTest(source=source), self.assertRaises(gates.Refusal):
                gates.validate(ROOT, source.encode())

    def test_report_escape_and_receipt_mutation_refuse(self):
        command = 'python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}'
        with self.assertRaises(gates.Refusal):
            gates.validate_command(ROOT, command, {'format': 'unittest-json-v1', 'file': '../out.json'})
        source = ('```sh\n' + COMMAND + '\n```\n').encode()
        receipt = gates.validate(ROOT, source)
        for key in ('adapter_sha256', 'artifact_sha256'):
            wrong = copy.deepcopy(receipt)
            wrong[key] = '0' * 64
            with self.subTest(key=key), self.assertRaises(gates.Refusal):
                gates.replay(ROOT, source, wrong)

    def test_parser_binding_mutations_refuse_initial_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / BREVITAS
            path.parent.mkdir(parents=True)
            original = (ROOT / BREVITAS).read_text()
            changes = [original + '\nargparse.ArgumentParser = lambda *args, **kwargs: None\n',
                       original + '\nbuild_parser = lambda: None\n',
                       original.replace('    parser.add_argument("draft",', '    if True:\n        parser.add_argument("draft",'),
                       original.replace('    return parser', '    parser = None\n    return parser')]
            for candidate in changes:
                path.write_text(candidate)
                with self.subTest(candidate=candidate[-60:]), self.assertRaises(gates.Refusal):
                    gates.validate_command(root, COMMAND)

    def test_special_cli_and_indented_byte_custody(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / BREVITAS
            path.parent.mkdir(parents=True)
            os.mkfifo(path)
            with self.assertRaises(gates.Refusal):
                gates.validate_command(root, COMMAND)
        for command in ('  ' + COMMAND, '\nfor file in one.md\ndo\n' + COMMAND.replace('one.md', '\"$file\"') + '\ndone'):
            source = ('```sh\n' + command + '\n```\n').encode()
            receipt = gates.validate(ROOT, source)
            for record in receipt['commands']:
                raw = record['command'].encode()
                self.assertEqual(source[record['offset']:record['offset'] + len(raw)], raw)
            gates.replay(ROOT, source, receipt)


try:
    from .hexctl_harness import HexctlCase, hexctl_module
except ImportError:
    from hexctl_harness import HexctlCase, hexctl_module


class GateReceiptTests(HexctlCase):
    def test_current_report_receipt_survives_actual_checkpoint_relocation(self):
        import json
        try:
            from plugins.hexaemeron.tests.test_hexctl_checkpoint import HexctlCheckpointTests as helpers
        except ModuleNotFoundError:
            from test_hexctl_checkpoint import HexctlCheckpointTests as helpers
        runner = 'plugins/hexaemeron/tests/run_tests.py'
        for name in (BREVITAS, runner):
            self.write(name, (ROOT / name).read_text())
        self.git('add', BREVITAS, runner)
        self.git('commit', '-m', 'Fixture registered CLI sources')
        self.run_ctl('init', '--topic', 'Current gate checkpoint fixture')
        self.write_design_evidence()
        study = self.write('.hexaemeron/study.md', '# Study\n\n```risk-register\nsource | drift | replay\n```\n')
        self.run_ctl('done', 'study', '--artifact', study, '--skills', 'hexaemeron:protasis')
        text = '# Runbook\n\n'
        for number, title in ((1, 'First'), (2, 'Second')):
            tests = 'Interface.' if number == 1 else ('Elenchus command: `python3 ' + runner + ' --jobs 12 --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/reports/second.json`.')
            text += ('## Step ' + str(number) + ': ' + title + '\n\n**Goal.** Interface.\n**Entry.** Source.\n**Exit.** `' + COMMAND + '`\n**Files.** file.py\n**Tests.** ' + tests + '\n**Disciplines.** phylax: inert.\n\n')
        runbook = self.write('.hexaemeron/runbook.md', text)
        steps = self.write('.hexaemeron/steps.json', json.dumps(['First', 'Second']))
        self.run_ctl('done', 'runbook', '--artifact', runbook, '--steps-file', steps)
        state = self.state()
        receipt = copy.deepcopy(state['receipts']['runbook']['gate_commands'])
        for step in state['steps']:
            self.git('branch', self.step_branch(step['n'], state))
        self.run_ctl('record', 'security_suite', '"waived: fixture"')
        self.finish_step(1)
        capsule = Path(self.dir).resolve() / 'current-gate-capsule'
        payload = json.loads(self.run_ctl('checkpoint', 'export', '--out', str(capsule)).stdout)
        origin, _ = helpers.fresh_origin_for(self, capsule)
        helpers.restore_into(self, origin, capsule, payload['manifest_sha256'], environment=helpers.direct_environment(self))
        restored = helpers.restored_worktree(origin)
        restored_state = json.loads((restored / '.hexaemeron/state.json').read_bytes())
        self.assertNotEqual(str(restored), receipt['source_root'])
        self.assertEqual(restored_state['receipts']['runbook']['gate_commands'], receipt)
        gates.replay(restored, (restored / '.hexaemeron/runbook.md').read_bytes(), receipt)

    def current_run(self):
        self.run_ctl('init', '--topic', 'Current gate fixture')
        self.write_design_evidence()
        self.write(BREVITAS, (ROOT / BREVITAS).read_text())
        study = self.write('study.md', '# Study\n\n```risk-register\ncommand-drift | gate | compare source\n```\n')
        self.run_ctl('done', 'study', '--artifact', study, '--skills', 'hexaemeron:protasis')
        return self.state()

    def runbook(self, command=COMMAND):
        return self.write('runbook.md', '# Runbook\n\n## Step 1: Gate\n\n**Goal.** Validate.\n**Entry.** Source.\n**Exit.** `' + command + '`\n**Files.** file.py\n**Tests.** Test interface.\n**Disciplines.** phylax: no execution.\n')

    def test_current_init_and_refusal_precede_runbook_mutation(self):
        import json
        state = self.current_run()
        self.assertEqual(state['contracts']['gate_commands'], gates.SCHEMA)
        before = Path(self.target, '.hexaemeron/state.json').read_bytes()
        runbook = self.runbook(COMMAND + ' two.md three.md four.md')
        steps = self.write('steps.json', json.dumps(['Gate']))
        self.run_ctl('done', 'runbook', '--artifact', runbook, '--steps-file', steps, expect=1)
        self.assertEqual(Path(self.target, '.hexaemeron/state.json').read_bytes(), before)
        runbook = self.runbook()
        self.run_ctl('done', 'runbook', '--artifact', runbook, '--steps-file', steps)
        self.run_ctl('verify')
        receipt = self.state()['receipts']['runbook']['gate_commands']
        self.assertFalse(receipt['operation_ran'])
        self.assertEqual(receipt['commands'][0]['invocations'][0]['argv'][-1], 'one.md')

    def test_current_init_marker_cannot_be_downgraded(self):
        self.current_run()
        module = hexctl_module()
        state = self.state()
        del state['contracts']['gate_commands']
        module.commit(self.target, state, 'fixture:attempt-downgrade', {})
        result = self.run_ctl('verify', expect=1)
        self.assertIn('immutable init', result.stderr)
        status = self.run_ctl('status', '--field', 'gate_command_status')
        self.assertIn('stale-or-invalid', status.stdout)

    def test_full_cli_source_drift_blocks_mutation_then_fresh_amendment(self):
        import json
        self.current_run()
        runbook = self.runbook()
        steps = self.write('steps.json', json.dumps(['Gate']))
        self.run_ctl('done', 'runbook', '--artifact', runbook, '--steps-file', steps)
        path = Path(self.target, BREVITAS)
        path.write_text(path.read_text() + '\n# changed source, same parser\n')
        self.run_ctl('verify', expect=1)
        self.run_ctl('config', 'set', 'audit.max_rounds', '7', expect=1)
        candidate = self.write('candidate.md', Path(self.target, runbook).read_text() + self.runbook_amendment(verdicts='Step 1: entry holds; exit holds.', what='Complete replacement Exit: Run `' + COMMAND + '`.', touched='Step 1.'))
        self.run_ctl('amend', 'runbook', '--artifact', candidate)
        self.run_ctl('verify')

    def test_pending_amendment_recovers_after_actual_source_replacement(self):
        import argparse
        import json
        from unittest.mock import patch
        import os
        self.current_run()
        runbook = self.runbook()
        steps = self.write('steps.json', json.dumps(['Gate']))
        self.run_ctl('done', 'runbook', '--artifact', runbook, '--steps-file', steps)
        candidate = self.write('candidate.md', Path(self.target, runbook).read_text() + self.runbook_amendment(verdicts='Step 1: entry holds; exit holds.', what='Complete replacement Exit: Run `' + COMMAND + '`.', touched='Step 1.'))
        module = hexctl_module()
        replace = module._replace_runbook_bytes
        def interrupted(path, data):
            replace(path, data)
            raise RuntimeError('fixture interruption after actual replacement')
        before = self.state()
        with patch.dict(os.environ, self.env), patch.object(module, '_replace_runbook_bytes', interrupted):
            with self.assertRaisesRegex(RuntimeError, 'actual replacement'):
                module.cmd_amend_runbook(argparse.Namespace(dir=self.target, artifact=str(Path(self.target, candidate))))
        self.assertEqual(self.state(), before)
        self.assertIn('Complete replacement Exit:', Path(self.target, runbook).read_text())
        self.assertTrue(module.pending_amendments(self.target))
        self.run_ctl('amend', 'runbook', '--artifact', candidate)
        self.assertFalse(module.pending_amendments(self.target))
        self.run_ctl('verify')

    def test_historical_fixture_remains_legacy_without_backfill(self):
        self.to_steps(titles=('Legacy',))
        self.assertNotIn('gate_commands', self.state()['contracts'])
        self.assertNotIn('gate_commands', self.state()['receipts']['runbook'])
        self.run_ctl('verify')


class GateReportTests(unittest.TestCase):
    def test_source_owned_report_bytes_and_relative_declaration(self):
        import json
        import os
        import sys
        import time
        try:
            from plugins.hexaemeron.tests import run_tests as producer
        except ModuleNotFoundError:
            import run_tests as producer
        elenchus_path = ROOT / 'plugins/hexaemeron/skills/elenchus/scripts/elenchus.py'
        specification = importlib.util.spec_from_file_location('gate_elenchus_owner', elenchus_path)
        owner = importlib.util.module_from_spec(specification)
        sys.modules[specification.name] = owner
        specification.loader.exec_module(owner)
        source_command = 'python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            script = root / 'plugins/hexaemeron/tests/run_tests.py'
            script.parent.mkdir(parents=True)
            script.write_bytes(Path(producer.__file__).read_bytes())
            declaration = {'format': 'unittest-json-v1', 'file': '.hexaemeron/reports/specimen.json'}
            binding = gates.validate_command(root, source_command, declaration)
            absolute = binding['invocations'][0]['execution_argv'][-1]
            prior = Path.cwd()
            try:
                os.chdir(root)
                target = producer.bind_report_target(absolute, producer.argument_parser())
                started = time.time_ns()
                result = unittest.TestResult()
                unittest.FunctionTestCase(lambda: self.assertEqual(2 + 2, 4)).run(result)
                payload = producer.result_payload(result)
                producer.write_report(target, payload)
                raw = Path(absolute).read_bytes()
                normal = owner.read_report(Path(absolute), declaration['format'], started, root)
                self.assertEqual(normal.executed, 1)
                self.assertEqual(Path(absolute).read_bytes(), raw)
                self.assertEqual(json.loads(raw)['schema'], 'elenchus.unittest.v1')
                self.assertEqual(binding['report']['file'], '.hexaemeron/reports/specimen.json')
                self.assertEqual(binding['command'], source_command)
                self.observations = {'relative-source-declaration-preserved': binding['report'],
                    'absolute-execution-destination': absolute,
                    'report-bytes-preserved': {'sha256': gates.digest(raw), 'bytes': len(raw), 'producer_schema': payload['schema'], 'format': declaration['format'], 'actual_testsRun': result.testsRun, 'raw_utf8': raw.decode('utf-8')}}
                for bad in ('../outside.json', '.git/report.json'):
                    with self.assertRaises(gates.Refusal):
                        gates.validate_command(root, source_command, {'format': declaration['format'], 'file': bad})
                self.observations['report-escape-refused'] = ['../outside.json', '.git/report.json']
            finally:
                os.chdir(prior)


class GateConformanceTests(unittest.TestCase):
    def test_inert_parser_specimens(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / BREVITAS
            target.parent.mkdir(parents=True)
            target.write_bytes((ROOT / BREVITAS).read_bytes())
            marker = root / 'unexpected-effect'
            commands = {
                'malformed-fence': '```sh\n' + COMMAND + '\n~~~\n',
                'four-draft-brevitas': '```sh\n' + COMMAND + ' two.md three.md four.md\n```\n',
                'unsupported-substitution': '```sh\n' + COMMAND + ' $(echo injected)\n```\n',
                'injected-command-no-side-effect': '```sh\n' + COMMAND + '; touch ' + str(marker) + '\n```\n',
            }
            self.observations = {}
            for name, source in commands.items():
                with self.subTest(name=name), self.assertRaises(gates.Refusal) as caught:
                    gates.validate(root, source.encode())
                self.assertFalse(marker.exists())
                self.observations[name] = {'source': source, 'refusal': str(caught.exception), 'marker_exists': False, 'operation_ran': False}

    def test_exact_replay_specimens(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / BREVITAS
            path.parent.mkdir(parents=True)
            original = (ROOT / BREVITAS).read_bytes()
            path.write_bytes(original)
            command = 'for file in one.md "two drafts.md"; do ' + COMMAND.replace('one.md', '"$file"') + '; done'
            source = ('```sh\n' + command + '\n```\n').encode()
            receipt = gates.validate(root, source)
            gates.replay(root, source, receipt)
            self.observations = {'finite-per-file-command': receipt}
            changed = source.replace(b'one.md', b'changed.md')
            with self.assertRaises(gates.Refusal) as caught:
                gates.replay(root, changed, receipt)
            self.observations['command-drift'] = {'refusal': str(caught.exception), 'changed_sha256': gates.digest(changed)}
            path.write_bytes(original + b'\n# independently changed CLI source\n')
            with self.assertRaises(gates.Refusal) as caught:
                gates.replay(root, source, receipt)
            self.observations['cli-source-drift'] = {'refusal': str(caught.exception), 'changed_sha256': gates.digest(path.read_bytes())}
            path.write_bytes(original)
            adapter = root / 'changed_adapter.py'
            adapter.write_bytes(SOURCE.read_bytes() + b'\n# independently changed adapter source\n')
            specification = importlib.util.spec_from_file_location('changed_gate_adapter_fixture', adapter)
            changed_module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(changed_module)
            with self.assertRaises(changed_module.Refusal) as caught:
                changed_module.replay(root, source, receipt)
            self.observations['adapter-drift'] = {'refusal': str(caught.exception), 'changed_sha256': gates.digest(adapter.read_bytes())}
            runner = root / 'plugins/hexaemeron/tests/run_tests.py'
            runner.parent.mkdir(parents=True, exist_ok=True)
            runner.write_bytes((ROOT / 'plugins/hexaemeron/tests/run_tests.py').read_bytes())
            source = b'## Step 1: Reports\n**Tests.** Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/reports/one.json`.\n'
            receipt = gates.validate(root, source)
            changed = source.replace(b'one.json', b'two.json')
            with self.assertRaises(gates.Refusal) as caught:
                gates.replay(root, changed, receipt)
            self.observations['report-source-drift'] = {'refusal': str(caught.exception), 'original': '.hexaemeron/reports/one.json', 'changed': '.hexaemeron/reports/two.json'}


if __name__ == '__main__':
    unittest.main()
