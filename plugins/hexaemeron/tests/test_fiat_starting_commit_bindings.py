"""Starting-commit bindings the controller derives: admission, refusal, status, proof.

Each run here is initialised and receipted under a copy of this controller
whose adapter pins one registered module at another digest, with that adapter
and module committed at the fixture's base commit, and is then read under this
controller. Git is real and every receipted commit is signed with the fixture's
own key; the fake GitHub client answers the platform reads. Nothing reads the
plugin cache, the network or this repository's history.
"""
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture_tools import native_signing_tools
from hexctl_harness import HEXCTL, HexctlCase, hexctl_module

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = 'plugins/hexaemeron/skills/protasis/scripts/gate_commands.py'
PROOF = 'plugins/hexaemeron/tests/fiat_starting_commit_bindings_proof.py'
BREVITAS = 'plugins/brevitas/skills/brevitas/scripts/brevitas.py'
RUN_CHECKS = 'scripts/run_checks.py'
COMMAND = 'python3 ' + BREVITAS + ' one.md'
RUNBOOK = ('# Runbook\n\n## Step 1: Gate\n\n**Goal.** Validate.\n**Entry.** Source.\n'
           '**Exit.** `' + COMMAND + '`\n**Files.** file.py\n**Tests.** Test interface.\n'
           '**Disciplines.** phylax: no execution.\n')
STUDY = '# Study\n\n```risk-register\ncontroller-skew | gate | name the recorded controller\n```\n'
FIXTURE_CRITERION = 'older-controller-supersession-fixture'
FIXTURE_MODULE = 'plugins.hexaemeron.tests.test_fiat_starting_commit_bindings'
# A registered interface as a run's starting commit shipped it. Its module-level
# AST differs from this controller's pin, so this controller refuses it alone.
MODULE_PROGRAM = '''"""A registered interface, unchanged since its run's starting commit."""
import argparse

REVISION = "starting-commit"


def build_parser():
    parser = argparse.ArgumentParser(description="Fixture registered interface.")
    parser.add_argument("draft", nargs="+")
    parser.add_argument("--format", choices=["human", "json"], default="human")
    return parser
'''
UNNAMED_PROGRAM = MODULE_PROGRAM.replace('"starting-commit"', '"unnamed-at-base"')
PIN_SKEW = 'pinned at different commits'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gates = load(ROOT / ADAPTER, 'starting_commit_gate')
proof = load(ROOT / PROOF, 'starting_commit_proof')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ast_pin(source, builder='build_parser'):
    """The module digest exactly as ``parser_bindings`` computes it."""
    tree = ast.parse(source)
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == builder]
    functions[0].body = []
    return sha(ast.dump(tree, include_attributes=False).encode())


def near_miss(digest, index=-1):
    """``digest`` with one hexadecimal character changed: still 64 lowercase hex."""
    position = index % len(digest)
    replacement = '0' if digest[position] != '0' else '1'
    return digest[:position] + replacement + digest[position + 1:]


def repinned_adapter(pins):
    """This controller's adapter text with the given registered modules re-pinned."""
    text = (ROOT / ADAPTER).read_text()
    for path, pin in pins.items():
        current = gates.MODULE_BINDINGS[path]
        if text.count(current) != 1:
            raise AssertionError('adapter pin for ' + path + ' is not unique')
        text = text.replace(current, pin)
    return text


def unreadable_pins(text):
    """The same adapter with its pin table built by a call, which is not a literal."""
    start = text.index('MODULE_BINDINGS = {')
    end = text.index('\n', start)
    line = text[start:end]
    assert line.endswith('}')
    return text[:start] + 'MODULE_BINDINGS = dict(' + line[len('MODULE_BINDINGS = '):] + ')' + text[end:]


class StartingCommitRun(HexctlCase):
    """A real repository with the fixture's own signing key and the fake GitHub client."""

    @classmethod
    def setUpClass(cls):
        cls.tools_context = native_signing_tools()
        cls.tools = cls.tools_context.__enter__()
        # The agent creates several sockets; keep the home short for macOS AF_UNIX.
        cls.temporary = tempfile.TemporaryDirectory(prefix='fs-')
        cls.home = Path(cls.temporary.name) / 'h'
        cls.home.mkdir(mode=0o700)
        socket_path = os.path.realpath(cls.home / 'S.gpg-agent.browser')
        if len(os.fsencode(socket_path)) >= 104:
            raise AssertionError('fixture GPG agent socket path is too long: ' + socket_path)
        cls.signing_env = {'GNUPGHOME': str(cls.home)}
        generated = subprocess.run(  # phylax: allow subprocess: fixed argv, no shell
            [cls.tools['gpg'], '--batch', '--pinentry-mode', 'loopback', '--passphrase', '',
             '--quick-generate-key', 'Fixture <fixture@example.invalid>', 'ed25519', 'sign', '0'],
            env={**os.environ, **cls.signing_env}, capture_output=True, timeout=30)
        if generated.returncode:
            raise AssertionError('fixture GPG key generation exited %d: %s' % (
                generated.returncode, generated.stderr.decode('utf-8', 'replace')[:2048]))
        cls.module = hexctl_module()

    @classmethod
    def tearDownClass(cls):
        subprocess.run([cls.tools['gpgconf'], '--homedir', str(cls.home), '--kill', 'gpg-agent'],  # phylax: allow subprocess: fixed argv, no shell
                       check=False, capture_output=True, timeout=10)
        cls.temporary.cleanup()
        cls.tools_context.__exit__(None, None, None)

    def setUp(self):
        super().setUp()
        # The harness's fake git answers refs for a fixture with no history. This
        # fixture has one, and its signatures are real, so only the fake GitHub
        # client stays on the path.
        os.remove(os.path.join(self.dir, 'delivery-tools', 'git'))
        self.env.update(self.signing_env)
        for key, value in (('commit.gpgsign', 'true'), ('user.signingkey', 'fixture@example.invalid'),
                           ('gpg.format', 'openpgp')):
            self.origin_git('config', key, value)
        self.origin_git('remote', 'add', 'origin', 'https://github.com/wildcat-finance/example.git')

    def repo_git(self, cwd, *args):
        completed = subprocess.run(['git', *args], cwd=cwd, env=self.env, capture_output=True,  # phylax: allow subprocess: fixed argv, no shell
                                   text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        return completed.stdout.strip()

    def origin_git(self, *args):
        return self.repo_git(self.dir, *args)

    def target_git(self, *args):
        return self.repo_git(self.target, *args)

    def base_commit(self, files):
        """Commit `files` on the origin's main and return the commit id."""
        for relative, text in files.items():
            path = Path(self.dir, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            self.origin_git('add', relative)
        self.origin_git('commit', '-q', '-S', '-m', 'Fixture base')
        return self.origin_git('rev-parse', 'HEAD')

    def controller(self, adapter_text, version='fiat-v9.99.9'):
        """A copy of this controller outside any repository, carrying `adapter_text`."""
        home = tempfile.mkdtemp(prefix='fs-ctl-')
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        skills = Path(home, 'plugins', 'hexaemeron', 'skills')
        # The receipts resolve the sibling checkers beside the controller, so
        # every skill's scripts travel with the copy; only the adapter differs.
        for scripts in sorted((ROOT / 'plugins/hexaemeron/skills').glob('*/scripts')):
            shutil.copytree(scripts, skills / scripts.parent.name / 'scripts',
                            ignore=shutil.ignore_patterns('__pycache__'))
        ledger = (ROOT / 'plugins/hexaemeron/skills/fiat/EVOLUTION.md').read_text()
        lines = [line for line in ledger.splitlines(keepends=True) if line.startswith('- Current version:')]
        self.assertEqual(len(lines), 1)
        (skills / 'fiat/EVOLUTION.md').write_text(
            ledger.replace(lines[0], '- Current version: `' + version + '`\n'))
        (skills / 'protasis/scripts/gate_commands.py').write_text(adapter_text)
        return str(skills / 'fiat/scripts/hexctl.py')

    def run_controller(self, controller, *args, expect=0, cwd=None):
        completed = subprocess.run([sys.executable, controller, *args], cwd=cwd or self.target,  # phylax: allow subprocess: fixed argv interpreter, no shell
                                   capture_output=True, text=True, env=self.env, timeout=300)
        self.assertEqual(completed.returncode, expect, completed.stdout + completed.stderr)
        return completed

    def receipted_run(self, controller, *, study=STUDY, implement=True):
        """Drive init, study, runbook and a signed implementation receipt under `controller`.

        A study that declares a criterion stops at the runbook receipt: its
        implementation receipt would need an observed execution first.
        """
        self.run_controller(controller, 'init', '--topic', 'Starting commit fixture', cwd=self.dir)
        self.write_design_evidence()
        study_path = self.write('study.md', study)
        self.run_controller(controller, 'done', 'study', '--artifact', study_path,
                            '--skills', 'hexaemeron:protasis')
        runbook = self.write('runbook.md', self.design_lock_block() + '\n' + RUNBOOK)
        steps = self.write('steps.json', json.dumps(['Gate']))
        self.run_controller(controller, 'done', 'runbook', '--artifact', runbook, '--steps-file', steps)
        state = self.state()
        if not implement:
            return state
        branch = self.step_branch(1, state)
        self.target_git('switch', '-q', '-c', branch)
        Path(self.target, 'step-1.txt').write_text('tree content for the receipt\n')
        self.target_git('add', 'step-1.txt')
        self.target_git('commit', '-q', '-S', '-m', 'Step 1 implementation')
        commit = self.target_git('rev-parse', 'HEAD')
        self.run_controller(controller, 'done', 'implement', '--branch', branch, '--commit', commit)
        return self.state()

    def older_run(self, *, base_adapter='same', copy_adapter=None, unnamed=False, study=STUDY,
                  implement=True):
        """A run receipted under an older controller.

        `base_adapter` is the adapter text committed at the fixture's base, or
        None for none; 'same' commits the driving controller's adapter. The
        registered module committed at base is the one the runbook names, plus
        an unnamed second one when `unnamed`.
        """
        pins = {BREVITAS: ast_pin(MODULE_PROGRAM)}
        files = {BREVITAS: MODULE_PROGRAM}
        if unnamed:
            pins[RUN_CHECKS] = ast_pin(UNNAMED_PROGRAM)
            files[RUN_CHECKS] = UNNAMED_PROGRAM
        copy_adapter = copy_adapter or repinned_adapter(pins)
        if base_adapter == 'same':
            base_adapter = copy_adapter
        if base_adapter is not None:
            files[ADAPTER] = base_adapter
        base = self.base_commit(files)
        controller = self.controller(copy_adapter)
        state = self.receipted_run(controller, study=study, implement=implement)
        self.assertEqual(state['base'], base)
        return state, controller, copy_adapter

    def controller_snapshot(self):
        root = Path(self.target, '.hexaemeron')
        return {str(path.relative_to(root)): sha(path.read_bytes())
                for path in sorted(root.rglob('*')) if path.is_file()}

    def assert_refusal_writes_nothing(self, controller, cause, *args):
        before = self.controller_snapshot()
        result = self.run_controller(controller, *args, expect=1)
        self.assertIn(cause, result.stderr)
        self.assertEqual(self.controller_snapshot(), before)
        return result

    def gate_status(self, controller=HEXCTL):
        return json.loads(self.run_controller(controller, 'status', '--field', 'gate_command_status').stdout)


class OlderControllerRunTests(StartingCommitRun):
    def test_run_under_an_older_controller_verifies_and_supersedes_here(self):
        state, controller, adapter_text = self.older_run()
        self.run_controller(controller, 'verify')
        before = self.controller_snapshot()
        result = self.run_controller(HEXCTL, 'verify')
        self.assertIn('ok: ', result.stdout)
        self.assertEqual(self.controller_snapshot(), before)
        self.assertEqual(self.gate_status(), {
            'status': 'current', 'validation': 'interface-only',
            'provenance': {'starting_commit': state['base'],
                           'adapter_sha256': sha(adapter_text.encode()),
                           'modules': [BREVITAS]}})
        old = state['steps'][0]['receipts']['implement']['commit']
        self.target_git('commit', '--amend', '--no-edit', '-S', '-q')
        new = self.target_git('rev-parse', 'HEAD')
        self.assertNotEqual(old, new)
        self.assertEqual(self.target_git('rev-parse', old + '^{tree}'),
                         self.target_git('rev-parse', new + '^{tree}'))
        superseded = self.run_controller(HEXCTL, 'supersede-commit', '--old', old, '--new', new)
        self.assertIn('receipted; original receipt retained', superseded.stdout)
        state = self.state()
        self.assertEqual([(row['old'], row['new']) for row in state['steps'][0]['supersessions']], [(old, new)])
        events = [json.loads(line)['event'] for line in
                  Path(self.target, '.hexaemeron/ledger.jsonl').read_text().splitlines() if line.strip()]
        self.assertEqual(events[-1], 'commit:supersede')
        result = self.run_controller(HEXCTL, 'verify')
        self.assertIn('ok: ', result.stdout)
        self.assertEqual(self.gate_status()['status'], 'current')

    def test_criteria_admission_replays_under_the_starting_commit(self):
        study = (ROOT / 'plugins/hexaemeron/tests/fixtures/protasis/complete-study.md').read_text()
        study += '\n```success-criteria\n' + json.dumps({
            'schema': 'protasis-success-criteria/v1',
            'criteria': [{'id': 'checked', 'claim': 'The command succeeds.',
                          'step': 1, 'command': COMMAND}],
        }) + '\n```\n'
        state, controller, adapter_text = self.older_run(study=study, implement=False)
        admission = state['receipts']['runbook']['success_criteria']
        self.assertEqual(admission['gate_commands']['adapter_sha256'], sha(adapter_text.encode()))
        self.assertNotIn(sha(adapter_text.encode()), gates.REPLAY_COMPATIBLE_ADAPTERS)
        result = self.run_controller(HEXCTL, 'verify')
        self.assertIn('ok: ', result.stdout)
        criteria = json.loads(self.run_controller(HEXCTL, 'status', '--field', 'success_criteria_status').stdout)
        self.assertEqual(criteria['status'], 'current')
        self.assertEqual(self.gate_status()['provenance']['modules'], [BREVITAS])

    def test_edited_module_keeps_module_edited_in_run(self):
        self.older_run()
        path = Path(self.target, BREVITAS)
        path.write_text(path.read_text() + '\nbuild_parser_alias = build_parser\n')
        result = self.assert_refusal_writes_nothing(HEXCTL, 'unregistered-cli-module-bindings', 'verify')
        self.assertIn(BREVITAS + ' changed inside the run since its starting commit', result.stderr)
        self.assertNotIn(PIN_SKEW, result.stderr)
        status = self.gate_status()
        self.assertEqual(status['cause'], 'module-edited-in-run')
        self.assertEqual(status['modules'], [{'module': BREVITAS, 'since_base': 'changed', 'named_by_runbook': True}])

    def test_adapter_neither_reviewed_nor_the_base_keeps_gate_receipt_drift(self):
        base_adapter = repinned_adapter({BREVITAS: ast_pin(MODULE_PROGRAM)})
        copy_adapter = base_adapter + '\n# A later build of the same release.\n'
        state, controller, _ = self.older_run(base_adapter=base_adapter, copy_adapter=copy_adapter)
        receipt = state['receipts']['runbook']['gate_commands']['adapter_sha256']
        self.assertEqual(receipt, sha(copy_adapter.encode()))
        self.assertNotEqual(receipt, sha(base_adapter.encode()))
        self.assertNotIn(receipt, gates.REPLAY_COMPATIBLE_ADAPTERS)
        result = self.assert_refusal_writes_nothing(HEXCTL, 'gate-receipt-drift', 'verify')
        self.assertNotIn('unregistered-cli-module-bindings', result.stderr)
        status = self.gate_status()
        self.assertEqual(status['status'], 'stale-or-invalid')
        self.assertNotIn('cause', status)
        self.assertNotIn('modules', status)
        self.assertIn('submit a freshly validated runbook amendment', status['recovery'])

    def test_absent_base_adapter_keeps_controller_pin_skew_and_a_rewritten_base_writes_nothing(self):
        state, controller, _ = self.older_run(base_adapter=None)
        result = self.assert_refusal_writes_nothing(HEXCTL, 'unregistered-cli-module-bindings', 'verify')
        self.assertIn(BREVITAS + " is unchanged since the run's starting commit " + state['base'], result.stderr)
        self.assertIn(PIN_SKEW, result.stderr)
        self.assertIn('fiat-v9.99.9 at init', result.stderr)
        status = self.gate_status()
        self.assertEqual(status['cause'], 'controller-pin-skew')
        self.assertEqual(status['modules'], [{'module': BREVITAS, 'since_base': 'unchanged', 'named_by_runbook': True}])
        self.assertNotIn('provenance', status)
        # A base that is not a full commit id derives nothing and refuses before any write.
        rewritten = dict(state)
        rewritten['base'] = state['base'][:12]
        self.module.commit(self.target, rewritten, 'fixture:short-base', {})
        self.assert_refusal_writes_nothing(HEXCTL, 'hexctl: error:', 'verify')
        self.assertEqual(self.gate_status()['status'], 'stale-or-invalid')

    def test_unreadable_base_pins_keep_controller_pin_skew(self):
        adapter_text = unreadable_pins(repinned_adapter({BREVITAS: ast_pin(MODULE_PROGRAM)}))
        self.assertIn('MODULE_BINDINGS = dict({', adapter_text)
        state, controller, _ = self.older_run(base_adapter=adapter_text, copy_adapter=adapter_text)
        result = self.assert_refusal_writes_nothing(HEXCTL, PIN_SKEW, 'verify')
        self.assertIn('unregistered-cli-module-bindings', result.stderr)
        self.assertEqual(self.gate_status()['cause'], 'controller-pin-skew')

    def test_base_pin_disagreeing_with_the_module_keeps_controller_pin_skew(self):
        pin = ast_pin(MODULE_PROGRAM)
        state, controller, _ = self.older_run(
            base_adapter=repinned_adapter({BREVITAS: near_miss(pin, -1)}),
            copy_adapter=repinned_adapter({BREVITAS: pin}))
        result = self.assert_refusal_writes_nothing(HEXCTL, PIN_SKEW, 'verify')
        self.assertIn('unregistered-cli-module-bindings', result.stderr)
        status = self.gate_status()
        self.assertEqual(status['cause'], 'controller-pin-skew')
        self.assertEqual(status['modules'], [{'module': BREVITAS, 'since_base': 'unchanged', 'named_by_runbook': True}])

    def test_skew_list_marks_the_module_the_runbook_names(self):
        self.older_run(base_adapter=None, unnamed=True)
        self.assert_refusal_writes_nothing(HEXCTL, PIN_SKEW, 'verify')
        status = self.gate_status()
        self.assertEqual(status['cause'], 'controller-pin-skew')
        self.assertEqual(status['modules'], [
            {'module': BREVITAS, 'since_base': 'unchanged', 'named_by_runbook': True},
            {'module': RUN_CHECKS, 'since_base': 'unchanged', 'named_by_runbook': False}])

    def test_admitted_provenance_names_every_admitted_module(self):
        state, controller, adapter_text = self.older_run(unnamed=True)
        self.run_controller(HEXCTL, 'verify')
        self.assertEqual(self.gate_status()['provenance'], {
            'starting_commit': state['base'], 'adapter_sha256': sha(adapter_text.encode()),
            'modules': [BREVITAS, RUN_CHECKS]})

    def test_current_run_reads_no_git_for_this_rule(self):
        self.base_commit({BREVITAS: (ROOT / BREVITAS).read_text()})
        state = self.receipted_run(HEXCTL)
        before = self.controller_snapshot()
        self.run_controller(HEXCTL, 'verify')
        self.assertEqual(self.controller_snapshot(), before)
        self.assertEqual(self.gate_status(), {'status': 'current', 'validation': 'interface-only'})
        adapter = self.module.gate_commands_module()
        with mock.patch.dict(os.environ, self.env), \
                mock.patch.object(self.module, 'starting_commit_blob',
                                  side_effect=AssertionError('a current run read Git for this rule')), \
                mock.patch.object(self.module, 'starting_commit_module_bindings',
                                  side_effect=AssertionError('a current run parsed a base adapter')):
            self.assertIsNone(self.module.starting_commit_bindings(self.target, state, adapter))
            self.module.verify_run(self.target)

    def test_legacy_run_without_the_marker_stays_legacy(self):
        self.base_commit({BREVITAS: MODULE_PROGRAM})
        self.run_ctl('init', '--topic', 'Legacy fixture', historical_init=True)
        self.write_design_evidence()
        study = self.write('study.md', STUDY)
        self.run_ctl('done', 'study', '--artifact', study, '--skills', 'hexaemeron:protasis')
        runbook = self.write('runbook.md', self.design_lock_block() + '\n' + RUNBOOK)
        steps = self.write('steps.json', json.dumps(['Gate']))
        self.run_ctl('done', 'runbook', '--artifact', runbook, '--steps-file', steps)
        state = self.state()
        self.assertNotIn('gate_commands', state['contracts'])
        self.assertNotIn('gate_commands', state['receipts']['runbook'])
        before = self.controller_snapshot()
        self.run_controller(HEXCTL, 'verify')
        self.assertEqual(self.controller_snapshot(), before)
        self.assertEqual(self.gate_status(), {'status': 'legacy', 'validation': 'not-recorded'})
        with mock.patch.object(self.module, 'bounded_run',
                               side_effect=AssertionError('a legacy run read Git for this rule')):
            self.assertIsNone(self.module.starting_commit_bindings(
                self.target, state, self.module.gate_commands_module()))


class DerivationTests(unittest.TestCase):
    """The derivation on a scratch root, with the Git reads served from specimens."""

    def setUp(self):
        self.module = hexctl_module()
        self.adapter = self.module.gate_commands_module()
        directory = tempfile.TemporaryDirectory(prefix='starting-commit-derivation-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        path = self.root / BREVITAS
        path.parent.mkdir(parents=True)
        path.write_text(MODULE_PROGRAM)
        self.pin = ast_pin(MODULE_PROGRAM)
        self.state = {'contracts': {'gate_commands': gates.SCHEMA}, 'base': 'a' * 40}

    def derive(self, adapter_blob, module_blob=MODULE_PROGRAM.encode()):
        """Derive with the two base blobs served from memory; None stands for an absent blob."""
        served = {ADAPTER: adapter_blob, BREVITAS: module_blob}
        reads = []

        def blob(base_dir, starting, path):
            reads.append((starting, path))
            self.assertEqual(starting, self.state['base'])
            return served[path]

        with mock.patch.object(self.module, 'starting_commit_blob', side_effect=blob):
            result = self.module.starting_commit_bindings(str(self.root), self.state, self.adapter)
        return result, reads

    def test_exact_base_pin_admits_the_module_whole(self):
        blob = repinned_adapter({BREVITAS: self.pin}).encode()
        result, reads = self.derive(blob)
        self.assertEqual(result, {'adapter_sha256': sha(blob), 'modules': {
            BREVITAS: {'ast_sha256': self.pin, 'source_sha256': sha(MODULE_PROGRAM.encode())}}})
        self.assertEqual(reads, [(self.state['base'], ADAPTER), (self.state['base'], BREVITAS)])
        self.assertIsNotNone(gates.starting_bindings_admitted(result))

    def test_near_miss_base_pins_admit_nothing(self):
        specimens = {
            'last-character': near_miss(self.pin, -1),
            'first-character': near_miss(self.pin, 0),
            'prefix': self.pin[:63],
            'uppercase': self.pin.upper(),
            'another-module-only': None,
        }
        for label, pin in specimens.items():
            with self.subTest(label=label):
                if pin is None:
                    text = repinned_adapter({})
                    entry = "'" + BREVITAS + "': '" + gates.MODULE_BINDINGS[BREVITAS] + "', "
                    self.assertEqual(text.count(entry), 1)
                    blob = text.replace(entry, '').encode()
                else:
                    blob = repinned_adapter({BREVITAS: pin}).encode()
                self.assertIsNone(self.derive(blob)[0])

    def test_module_bytes_differing_from_the_base_blob_admit_nothing(self):
        blob = repinned_adapter({BREVITAS: self.pin}).encode()
        for label, recorded in (('one-byte', MODULE_PROGRAM.encode() + b'\n'),
                                ('absent', None)):
            with self.subTest(label=label):
                self.assertIsNone(self.derive(blob, recorded)[0])

    def test_unreadable_base_adapter_admits_nothing(self):
        text = repinned_adapter({BREVITAS: self.pin})
        specimens = {
            'absent': None,
            'not-python': b'this is not python (',
            'call-not-literal': unreadable_pins(text).encode(),
            'two-assignments': (text + '\nMODULE_BINDINGS = {}\n').encode(),
            'annotated': text.replace('MODULE_BINDINGS = {', 'MODULE_BINDINGS: dict = {').encode(),
            'non-string-value': text.replace("'" + self.pin + "'", '1').encode(),
            'tuple-target': text.replace('MODULE_BINDINGS = {', 'MODULE_BINDINGS, OTHER = {', 1).replace(
                '}\nFENCE', '}, 1\nFENCE', 1).encode(),
        }
        for label, blob in specimens.items():
            with self.subTest(label=label):
                self.assertIsNone(self.derive(blob)[0])
                if blob is not None:
                    self.assertIsNone(self.module.starting_commit_module_bindings(blob))

    def test_no_refused_module_or_no_marker_or_short_base_reads_no_git(self):
        pin_table = self.module.starting_commit_module_bindings
        with mock.patch.object(self.module, 'bounded_run', side_effect=AssertionError('read Git')):
            for label, state in (
                    ('no-marker', {'contracts': {}, 'base': 'a' * 40}),
                    ('short-base', {'contracts': {'gate_commands': gates.SCHEMA}, 'base': 'a' * 39}),
                    ('uppercase-base', {'contracts': {'gate_commands': gates.SCHEMA}, 'base': 'A' * 40}),
                    ('missing-base', {'contracts': {'gate_commands': gates.SCHEMA}})):
                with self.subTest(label=label):
                    self.assertIsNone(self.module.starting_commit_bindings(str(self.root), state, self.adapter))
            (self.root / BREVITAS).write_text((ROOT / BREVITAS).read_text())
            self.assertIsNone(self.module.starting_commit_bindings(str(self.root), self.state, self.adapter))
        self.assertIs(self.module.starting_commit_module_bindings, pin_table)

    def test_admission_helper_retries_only_on_the_pin_refusal(self):
        calls = []
        bindings = {'adapter_sha256': 'ab' * 32, 'modules': {}}

        def operation(starting):
            calls.append(starting)
            if starting is None:
                raise self.adapter.Refusal('unregistered-cli-module-bindings')
            return 'admitted'

        with mock.patch.object(self.module, 'starting_commit_bindings', return_value=bindings) as derive:
            self.assertEqual(self.module.admit_with_starting_bindings(str(self.root), self.state, self.adapter, operation),
                             ('admitted', bindings))
        self.assertEqual(calls, [None, bindings])
        derive.assert_called_once_with(str(self.root), self.state, self.adapter)
        calls.clear()
        with mock.patch.object(self.module, 'starting_commit_bindings', return_value=None) as derive:
            with self.assertRaisesRegex(self.adapter.Refusal, '^unregistered-cli-module-bindings$'):
                self.module.admit_with_starting_bindings(str(self.root), self.state, self.adapter, operation)
        self.assertEqual(calls, [None])
        derive.assert_called_once()

        def other(starting):
            raise self.adapter.Refusal('gate-receipt-drift')

        with mock.patch.object(self.module, 'starting_commit_bindings') as derive:
            with self.assertRaisesRegex(self.adapter.Refusal, '^gate-receipt-drift$'):
                self.module.admit_with_starting_bindings(str(self.root), self.state, self.adapter, other)
        derive.assert_not_called()
        with mock.patch.object(self.module, 'starting_commit_bindings') as derive:
            self.assertEqual(self.module.admit_with_starting_bindings(
                str(self.root), self.state, self.adapter, lambda starting: ('fast', starting)), (('fast', None), None))
        derive.assert_not_called()

    def test_skew_list_excludes_admitted_modules_and_marks_named_ones(self):
        blob = repinned_adapter({BREVITAS: self.pin}).encode()
        bindings = self.derive(blob)[0]
        skew = self.module.registered_module_skew(str(self.root), self.state, self.adapter)
        self.assertEqual(skew, [{'module': BREVITAS, 'since_base': 'unknown', 'named_by_runbook': False}])
        named = self.module.registered_module_skew(str(self.root), self.state, self.adapter, runbook=RUNBOOK.encode())
        self.assertEqual(named, [{'module': BREVITAS, 'since_base': 'unknown', 'named_by_runbook': True}])
        unnamed = self.module.registered_module_skew(
            str(self.root), self.state, self.adapter, runbook=RUNBOOK.replace(BREVITAS, RUN_CHECKS).encode())
        self.assertEqual(unnamed[0]['named_by_runbook'], False)
        self.assertEqual(self.module.registered_module_skew(
            str(self.root), self.state, self.adapter, starting_bindings=bindings), [])
        self.assertEqual(self.module.runbook_named_modules(self.adapter, b'\xff\xfe not a document'), frozenset())
        self.assertEqual(self.module.runbook_named_modules(self.adapter, None), frozenset())


class ProofReporterTests(unittest.TestCase):
    RESOLVER = ('python3 ' + PROOF + ' --candidate base-commit-bindings --criterion ' + FIXTURE_CRITERION
                + ' --report .hexaemeron/reports/design/base-commit-bindings-' + FIXTURE_CRITERION + '.json')

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='starting-bindings-proof-')
        self.addCleanup(directory.cleanup)
        self.scratch = Path(directory.name).resolve()
        self.report = self.scratch / 'report.json'

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = proof.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_design_record_names_this_handler_and_this_module(self):
        record = json.loads((ROOT / 'docs/starting-commit-gate-bindings/design-evidence.json').read_bytes())
        resolvers = {row['criterion']: row['resolver'] for row in record['results']
                     if row['candidate'] == 'base-commit-bindings' and row['state'] == 'pending'}
        self.assertEqual(resolvers[FIXTURE_CRITERION], self.RESOLVER)
        self.assertEqual(proof.NOT_IMPLEMENTED, {})
        self.assertEqual(proof.FIXTURE_CRITERION, FIXTURE_CRITERION)
        self.assertEqual(proof.FIXTURE_MODULES, (FIXTURE_MODULE,))
        self.assertTrue((ROOT / FIXTURE_MODULE.replace('.', '/')).with_suffix('.py').is_file())

    def test_green_fixture_module_writes_one_closed_report(self):
        completed = subprocess.CompletedProcess(['python3'], 0, b'', b'')
        with mock.patch.object(proof.subprocess, 'run', return_value=completed) as spy:
            code, out, err = self.run_main('--candidate', 'base-commit-bindings',
                                           '--criterion', FIXTURE_CRITERION, '--report', str(self.report))
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(out, 'base-commit-bindings/' + FIXTURE_CRITERION + ' = True\n')
        self.assertEqual(spy.call_args.args[0], [sys.executable, '-m', 'unittest', FIXTURE_MODULE])
        self.assertEqual(spy.call_args.kwargs['cwd'], ROOT)
        written = json.loads(self.report.read_bytes())
        self.assertEqual(written, {
            'schema': 'protasis-design-report/v1', 'candidate': 'base-commit-bindings',
            'criterion': FIXTURE_CRITERION, 'value': True, 'unit': 'boolean',
            'command': 'python3 ' + PROOF + ' --candidate base-commit-bindings --criterion '
                       + FIXTURE_CRITERION + ' --report ' + str(self.report),
            'exit': 0})
        with mock.patch.object(proof.subprocess, 'run', return_value=completed):
            code, _, err = self.run_main('--candidate', 'base-commit-bindings',
                                         '--criterion', FIXTURE_CRITERION, '--report', str(self.report))
        self.assertEqual((code, err), (1, 'refused: report-already-exists\n'))
        self.assertEqual(json.loads(self.report.read_bytes()), written)

    def test_red_fixture_module_writes_nothing(self):
        completed = subprocess.CompletedProcess(['python3'], 1, b'', b'FAILED')
        with mock.patch.object(proof.subprocess, 'run', return_value=completed):
            code, out, err = self.run_main('--candidate', 'base-commit-bindings',
                                           '--criterion', FIXTURE_CRITERION, '--report', str(self.report))
        self.assertEqual((code, out, err), (1, '', 'refused: older-controller-fixture-red: exit 1\n'))
        self.assertEqual(sorted(os.listdir(self.scratch)), [])


if __name__ == '__main__':
    unittest.main()
