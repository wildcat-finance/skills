"""Join real local custody and native execution with disposable delivery transitions."""

from contextlib import redirect_stdout
from io import StringIO
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from hexctl_harness import HexctlCase, LINTS_CLEAN, hexctl_module
from fixture_tools import native_signing_tools
import test_carryover as packet_cases
from test_carryover import ISSUE, SOURCE, carryover

ROOT = Path(__file__).resolve().parents[3]
CLI = 'plugins/brevitas/skills/brevitas/scripts/brevitas.py'


@unittest.skipUnless(sys.platform == 'darwin', 'native macOS policy required')
class ConfinedReplacementLifecycleTests(unittest.TestCase):
    def fixture(self):
        case = HexctlCase(); case.setUp()
        self.addCleanup(case.tearDown)
        self.addCleanup(case.doCleanups)
        return case

    def test_exhausted_source_to_current_gate_audit_and_integration(self):
        tool_paths = self.enterContext(native_signing_tools())
        self.observations = {}
        old = self.fixture(); old.to_audit(task_issue=ISSUE)
        helper = packet_cases.InoculationBodyTests(); helper.setUp(); self.addCleanup(helper.doCleanups)
        execution = helper.request()
        for name in ('calc.py', 'guards.py'):
            (Path(old.target) / name).write_bytes((helper.root / name).read_bytes())
        old.git('add', 'calc.py', 'guards.py'); old.git('commit', '-m', 'Preserved candidate and behavior guard')
        old.run_ctl('record', 'security_suite', '"waived: fixture"')
        for _ in range(7): old.run_ctl('audit-round', '--findings', '1', *LINTS_CLEAN)
        args = ('audit-round', '--findings', '1', '--fixes-commit', 'pending', '--elenchus-verdict', 'unguarded', *LINTS_CLEAN)
        old.append_valid_audit_record(args, old.state())
        keytemporary = tempfile.TemporaryDirectory(prefix='fiat-key-'); self.addCleanup(keytemporary.cleanup)
        keyhome = Path(keytemporary.name); keyhome.chmod(0o700)
        env = {**os.environ, 'GNUPGHOME': str(keyhome)}
        old.env['GNUPGHOME'] = str(keyhome)
        key = subprocess.run([tool_paths['gpg'], '--batch', '--pinentry-mode', 'loopback', '--passphrase', '',
                              '--quick-generate-key', 'Lifecycle Fixture <fixture@example.invalid>',
                              'ed25519', 'sign', '0'], env=env, capture_output=True, timeout=30)
        self.assertEqual(key.returncode, 0, key.stderr.decode())
        self.addCleanup(subprocess.run, [tool_paths['gpgconf'], '--homedir', str(keyhome), '--kill', 'gpg-agent'],
                        capture_output=True, check=False, timeout=10)
        message = 'Fixed candidate\n\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\nWildcat-Origin: shoggoth\n'
        subprocess.run(['git', '-c', 'user.signingkey=fixture@example.invalid', '-c', 'gpg.format=openpgp',
                        'commit', '--allow-empty', '-S', '-m', message], cwd=old.target, env=env,
                       check=True, capture_output=True, timeout=30)
        fixed = old.git('rev-parse', 'HEAD').stdout.strip()
        old.git('branch', '-f', old.step_branch(1), fixed); old.auto_audit_records = False
        old.run_ctl('audit-round', '--findings', '1', '--fixes-commit', fixed,
                    '--elenchus-verdict', 'unguarded', *LINTS_CLEAN)
        old.git('update-ref', 'refs/heads/lifecycle-proof', fixed)
        controller = hexctl_module()
        self.enterContext(mock.patch.dict(sys.modules, {controller.__name__: controller}))
        spec = importlib.util.spec_from_file_location('lifecycle_replacement', SOURCE.with_name('replacement.py'))
        replacement = importlib.util.module_from_spec(spec); spec.loader.exec_module(replacement)
        capsule = Path(old.dir).resolve() / 'capsule'
        packet = Path(old.dir).resolve() / '508-CARRYOVER.md'
        with mock.patch.dict(os.environ, env), redirect_stdout(StringIO()) as output:
            controller.cmd_checkpoint_export(SimpleNamespace(dir=old.target, out=str(capsule)))
        manifest = json.loads(output.getvalue())['manifest_sha256']
        with mock.patch.dict(os.environ, env):
            exported = carryover.export(controller, old.target, {'archive': str(capsule),
                'manifest_sha256': manifest, 'fixed_ref': 'refs/heads/lifecycle-proof', 'previous': None, 'out': str(packet)})
        proof = Path(old.dir).resolve() / 'proof.git'
        subprocess.run(['git', 'clone', '--mirror', old.target, str(proof)], check=True, capture_output=True, timeout=30)
        exhausted = old.state(); retired = Path(old.target)
        self.assertEqual(len(exhausted['steps'][0]['audit']['rounds']), 8)
        self.assertEqual(exhausted['steps'][0]['status'], 'open')
        old.run_ctl('halt', '--reason', 'replace exhausted fixture after packet export')
        with mock.patch.dict(os.environ, env):
            carryover.verify_receipts(controller, old.target, controller.load_state(old.target))
        with mock.patch.dict(old.env, {'PATH': os.environ['PATH']}):
            old.run_ctl('reset')
        self.assertFalse(retired.exists())
        self.observations['exhaust-export-retire'] = {'rounds': 8, 'source_step_closed': False,
            'packet_sha256': exported['packet_sha256'], 'fixed_commit': fixed,
            'archive_manifest_sha256': manifest, 'old_worktree_removed': True}
        fresh = self.fixture(); fresh.env['GNUPGHOME'] = str(keyhome)
        # Native source-proof reads use real Git; host delivery stays a fixture.
        shim = Path(fresh.env['PATH'].split(os.pathsep)[0]) / 'git'
        shim_source = shim.read_text()
        route = ('\nif os.path.realpath(os.getcwd()) == ' + repr(str(proof)) + ':\n'
                 '    os.execv(' + repr(shutil.which('git')) + ', [' + repr(shutil.which('git')) + ', *sys.argv[1:]])\n')
        shim.write_text(shim_source.replace('raw_args = sys.argv[1:]', route + '\nraw_args = sys.argv[1:]'))
        fresh.write(CLI, (ROOT / CLI).read_text())
        fresh.write('base-only.txt', 'complete independent base')
        fresh.git('add', CLI, 'base-only.txt'); fresh.git('commit', '-m', 'Current base with registered CLI')
        fresh.run_ctl('init', '--topic', 'Joined confined replacement', '--task-issue', ISSUE)
        fresh.write_design_evidence(); current = Path(fresh.target).resolve()
        self.assertEqual(fresh.state()['contracts']['gate_commands'], 'protasis-gate-commands/v1')
        with mock.patch.dict(os.environ, env):
            value = carryover.validate(controller, proof, packet.read_bytes(), exported['packet_sha256'])
        request = {'schema': 'fiat-replacement-request/v1', 'packet': {'path': str(packet), 'sha256': exported['packet_sha256']},
                   'proof_repository': str(proof), 'attachment': {'identity': '99',
                   'url': 'https://github.com/user-attachments/files/99/508-CARRYOVER.md'},
                   'files': [], 'occurrences': [], 'execution': execution}
        for row in value['files']:
            result = None if row['mode'] == 'delete' else {'mode': row['mode'], 'payload': row['payload']}
            request['files'].append({'source': row['path'], 'target': row['path'] if result else None,
                'disposition': 'unchanged', 'result': result, 'reason': 'preserve exact packet change',
                'base': {'source': None, 'target': None}})
        for source in value['passes']:
            for round_record in source['rounds']:
                for occurrence in round_record['occurrences']:
                    guard = execution['guards'][0]
                    request['occurrences'].append({'occurrence': replacement.occurrence_key(occurrence),
                        'guard': guard['id'], 'family': guard['family'], 'previous_guard': occurrence['guard'],
                        'previous_family': occurrence['family'], 'reason': 'current declaration; historical unknowns retained'})
        with mock.patch.dict(os.environ, env), mock.patch.object(replacement.packet, 'attachment_readback') as transport:
            pending = replacement.begin(controller, current, request)
            transport.assert_called_once_with(request['attachment'], exported['packet_sha256'], packet.stat().st_size)
            fresh.run_ctl('done', 'study', '--artifact', 'missing', expect=2)
            admitted = replacement.resume(controller, current)
        self.addCleanup(shutil.rmtree, admitted['private']['path'])
        stage = Path(admitted['stage']['path'])
        self.assertEqual((current / 'calc.py').read_bytes(), (helper.root / 'calc.py').read_bytes())
        self.assertEqual((current / 'base-only.txt').read_text(), 'complete independent base')
        self.assertEqual(len(request['occurrences']), 8)
        self.observations['complete-reconstruction'] = {'occurrences': 8,
            'base_only_sha256': carryover.digest((current / 'base-only.txt').read_bytes()), 'pending_status': pending['status']}
        self.observations['executed-inoculation'] = json.loads((stage / 'inoculation.json').read_bytes())
        self.assertTrue(admitted['fresh_independent_audit_required'])
        self.assertEqual(fresh.state()['steps'], [])
        study = fresh.write('study.md', '# Study\n\n```risk-register\nsource | drift | verify\n```\n')
        fresh.run_ctl('done', 'study', '--artifact', study, '--skills', 'hexaemeron:protasis')
        runbook = fresh.write('runbook.md', '# Runbook\n\n## Step 1: Joined\n\n**Goal.** Verify.\n**Entry.** Reconstruction.\n**Exit.** `python3 ' + CLI + ' draft.md`\n**Files.** calc.py\n**Tests.** Behavior.\n**Disciplines.** phylax: inert.\n')
        steps = fresh.write('steps.json', json.dumps(['Joined']))
        fresh.run_ctl('done', 'runbook', '--artifact', runbook, '--steps-file', steps)
        fresh.git('add', '.'); fresh.git('commit', '-m', 'Reconstructed current run')
        fresh.git('branch', fresh.step_branch(1))
        self.assertEqual(fresh.state()['steps'][0]['audit']['rounds'], [])
        fresh.run_ctl('record', 'security_suite', '"waived: fixture"')
        fresh.finish_step(1)
        self.assertEqual(len(fresh.state()['steps'][0]['audit']['rounds']), 1)
        self.observations['independent-audit'] = {'prior_audit_reused': False, 'new_fixture_rounds': 1,
            'finding_count': 0, 'scope': 'Controller transition fixture; independent product Warden remains separate.'}
        fresh.merge_stack(); fresh.write_run_pr()
        integrate = ('done', 'integrate', '--pr-url', 'https://github.com/wildcat-finance/example/pull/2',
                     '--merge-commit', 'f' * 40, '--closed-issue-url', ISSUE)
        with mock.patch.dict(os.environ, fresh.env):
            replacement.verify_receipt(controller, current, controller.load_state(str(current)))
        fresh.run_ctl('verify')
        refusals = []
        for name in ('capture.json', 'inoculation.json'):
            path = stage / name; raw = path.read_bytes()
            saved = stage / (name + '.fixture-held')
            for mutation in ('missing', 'changed'):
                before_state = (current / '.hexaemeron/state.json').read_bytes()
                before_ledger = (current / '.hexaemeron/ledger.jsonl').read_bytes()
                if mutation == 'missing':
                    path.rename(saved)
                else:
                    path.chmod(0o600); path.write_bytes(raw + b' ')
                try:
                    result = fresh.run_ctl(*integrate, expect=1)
                    self.assertIn('replacement admission receipt does not replay', result.stderr)
                    self.assertEqual((current / '.hexaemeron/state.json').read_bytes(), before_state)
                    self.assertEqual((current / '.hexaemeron/ledger.jsonl').read_bytes(), before_ledger)
                    refusals.append({'source': name, 'mutation': mutation, 'exit': result.returncode,
                                     'reason': result.stderr.strip()})
                finally:
                    if mutation == 'missing': saved.rename(path)
                    else: path.write_bytes(raw); path.chmod(0o400)
                fresh.run_ctl('verify')
        state_path = current / '.hexaemeron/state.json'
        state_bytes = state_path.read_bytes()
        missing = json.loads(state_bytes)
        del missing['receipts']['runbook']['gate_commands']
        state_path.write_text(json.dumps(missing))
        try:
            result = fresh.run_ctl(*integrate, expect=1)
            self.assertIn('gate recovery state differs from ledger', result.stderr)
            refusals.append({'source': 'runbook.gate_commands', 'mutation': 'missing',
                             'exit': result.returncode, 'reason': result.stderr.strip(),
                             'scope': 'State/ledger integrity refusal; no independent owner-receipt semantic claim.'})
        finally:
            state_path.write_bytes(state_bytes)
        fresh.run_ctl('verify')
        cli = current / CLI; original = cli.read_bytes(); cli.write_bytes(original + b'\n# independent drift\n')
        result = fresh.run_ctl(*integrate, expect=1)
        self.assertIn('gate', result.stderr.lower()); refusals.append({'source': CLI, 'exit': result.returncode})
        cli.write_bytes(original)
        with mock.patch.dict(os.environ, fresh.env):
            replacement.verify_receipt(controller, current, controller.load_state(str(current)))
        fresh.run_ctl('verify')
        fresh.run_ctl('--dir', str(current), 'verify')
        alias = Path(fresh.dir) / 'run-alias'
        alias.symlink_to(current, target_is_directory=True)
        controller_paths = [current / '.hexaemeron' / name for name in ('state.json', 'ledger.jsonl')]
        before_alias = [path.read_bytes() for path in controller_paths]
        refused = fresh.run_ctl('--dir', str(alias), 'verify', expect=2)
        self.assertIn('no-known transaction directory is not one stable no-follow directory',
                      refused.stderr)
        with self.assertRaisesRegex(replacement.worker.Refusal, 'unsafe-target-root'):
            replacement.verify_receipt(controller, alias, controller.load_state(str(current)))
        self.assertEqual(before_alias, [path.read_bytes() for path in controller_paths])
        alias.unlink()
        fresh.run_ctl('verify')
        self.observations['integration-refuses-mismatch'] = refusals
        receipt = fresh.state()['receipts']['runbook']['gate_commands']
        self.assertFalse(receipt['operation_ran'])
        fresh.run_ctl(*integrate)
        self.assertIn('integrate', fresh.state()['receipts'])
        self.observations['matching-launch-and-gate-evidence'] = {'capture_sha256': admitted['execution']['capture_sha256'],
            'report_sha256': admitted['execution']['report_sha256'], 'gate_artifact_sha256': receipt['artifact_sha256'],
            'integration_admitted': True, 'host_delivery': 'controlled fixture Git/GitHub responses; no external write'}
