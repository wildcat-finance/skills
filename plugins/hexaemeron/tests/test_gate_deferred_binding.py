"""Step 1's push binds a deferred runner, and the controller keeps that binding.

Every case drives the checked-in controller through the fake delivery tools in
a disposable Git fixture. The runner is written as data and never executed.
Each refusal is checked for its cause token and for unchanged state and ledger
bytes. The skills#1944 conformance resolver loads and runs this module as one
unit, so it imports only the shared harness.
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

try:
    from .hexctl_harness import COMPLETE_STUDY, HEXCTL, LINTS_CLEAN, HexctlCase, hexctl_module
except ImportError:
    from hexctl_harness import COMPLETE_STUDY, HEXCTL, LINTS_CLEAN, HexctlCase, hexctl_module

RUNNER = 'tests/run_tests.py'
RUNNER_PROGRAM = '''import argparse


def build_parser():
    parser = argparse.ArgumentParser(description="Run the fixture suite.")
    parser.add_argument("--elenchus-report", help="write a report to this fresh path")
    parser.add_argument("--pattern", default="test_*.py", help="discovery pattern")
    return parser
'''
STEP_ONE_EXIT = 'python3 ' + RUNNER + ' --pattern test_core.py'
STEP_TWO_EXIT = 'python3 ' + RUNNER
ELENCHUS = 'python3 ' + RUNNER + ' --elenchus-report {report}'
DEFERRED_ROW = RUNNER + ' | build_parser | step:1'
OTHER_RUNNER = 'tests/other_runner.py'
TITLES = ('Scaffold', 'Core')
PR_URL = 'https://github.com/wildcat-finance/example/pull/'


def fence(*rows):
    return ('```command-interfaces\nschema | protasis-command-interfaces/v1\n'
            + ''.join(row + '\n' for row in rows) + '```\n')


def runbook_text(rows=(DEFERRED_ROW,)):
    """A two-step runbook whose Step 1 and Step 2 commands name the runner."""
    text = '# Runbook\n\n'
    if rows is not None:
        text += fence(*rows) + '\n'
    exits = (STEP_ONE_EXIT, STEP_TWO_EXIT)
    for number, title in enumerate(TITLES, 1):
        text += (
            f'## Step {number}: {title}\n\n'
            f'**Goal.** Deliver {title.lower()}.\n'
            f'**Entry.** Step {number} is ready.\n'
            f'**Exit.** `{exits[number - 1]}`\n'
            f'**Files.** `{RUNNER}`\n'
            f'**Tests.** Elenchus command: `{ELENCHUS}`; format: `unittest-json-v1`; '
            f'report file: `.hexaemeron/reports/step-{number}-guard.json`.\n'
            '**Disciplines.** phylax: parse without imports.\n\n'
        )
    return text


def criteria_fence(step=2, command=STEP_TWO_EXIT):
    return '\n```success-criteria\n' + json.dumps({
        'schema': 'protasis-success-criteria/v1',
        'criteria': [{'id': 'runner-exit', 'claim': 'The runner accepts the Exit.',
                      'step': step, 'command': command}],
    }) + '\n```\n'


class DeferredBindingCase(HexctlCase):
    """One no-runner fixture run, driven step by step through the CLI."""

    def controller_bytes(self):
        root = Path(self.target, '.hexaemeron')
        return root.joinpath('state.json').read_bytes(), root.joinpath('ledger.jsonl').read_bytes()

    def head(self):
        return self.git('rev-parse', 'HEAD').stdout.strip()

    def gate_status(self):
        return json.loads(self.run_ctl('status', '--field', 'gate_command_status').stdout)

    def start(self, *, rows=(DEFERRED_ROW,), criteria=False, legacy=False, before_runbook=None):
        """Initialise, receipt the study and runbook, and cut both step branches."""
        self.run_ctl('init', '--topic', 'Deferred runner binding', historical_init=legacy)
        self.write_design_evidence()
        if criteria:
            study_text = Path(COMPLETE_STUDY).read_text(encoding='utf-8') + criteria_fence()
        else:
            study_text = '# Study\n\n```risk-register\nrunner | binding | replay\n```\n'
        study = self.write('.hexaemeron/study.md', study_text)
        self.run_ctl('done', 'study', '--artifact', study, '--skills', 'hexaemeron:protasis')
        runbook = self.write('.hexaemeron/runbook.md', runbook_text(rows))
        steps = self.write('.hexaemeron/steps.json', json.dumps(list(TITLES)))
        if before_runbook is not None:
            before_runbook()
        self.run_ctl('done', 'runbook', '--artifact', runbook, '--steps-file', steps)
        state = self.state()
        for step in state['steps']:
            self.git('branch', self.step_branch(step['n'], state))
        self.run_ctl('record', 'security_suite', '"waived: fixture"')
        self.runbook_path = Path(self.target, runbook)
        return state

    def create_runner(self, program=RUNNER_PROGRAM, *, commit=True):
        """Check out Step 1's branch and write the runner there."""
        self.git('checkout', '-q', self.step_branch(1))
        self.write(RUNNER, program)
        if commit:
            self.git('add', RUNNER)
            self.git('commit', '-q', '-m', 'Add the fixture runner')

    def implement_step_one(self):
        branch = self.step_branch(1)
        self.run_ctl('done', 'implement', '--branch', branch, '--commit', self.head())

    def audit_step_one(self):
        self.run_ctl('audit-round', '--findings', '0', *LINTS_CLEAN)
        self.run_ctl('done', 'audit')
        self.run_ctl('done', 'prose', '--files', '1',
                     '--skills', 'hexaemeron:imprimatur,hexaemeron:vulgate')

    def push(self, number=1, *, expect=0):
        head = self.head()
        branch, base = self.step_branch(number), self.step_base(number)
        # The fake remote learns the tip only after a successful push; a
        # refused one must still present the pushed branch at this head.
        # Each state read replaces the ref map, so write it last.
        self.fake_refs[branch] = head
        return self.run_ctl('done', 'push', '--pr-url', PR_URL + str(number),
                            '--head-commit', head, '--pr-base', base, expect=expect)

    def to_push_boundary(self, program=RUNNER_PROGRAM, **start):
        self.start(**start)
        self.create_runner(program)
        self.implement_step_one()
        self.audit_step_one()

    def to_bound(self, **start):
        self.to_push_boundary(**start)
        self.push()
        return self.state()['steps'][0]['receipts']['push']['gate_binding']

    def amend(self, what, touched='Step 1.', verdicts='Step 1: entry holds; exit holds. '
              'Step 2: entry holds; exit holds.', *, expect=0, name='candidate.md'):
        candidate = self.write(
            '.hexaemeron/' + name,
            self.runbook_path.read_text(encoding='utf-8')
            + self.runbook_amendment(verdicts=verdicts, what=what, touched=touched))
        return self.run_ctl('amend', 'runbook', '--artifact', candidate, expect=expect)

    def assert_refused_unchanged(self, action, token):
        before = self.controller_bytes()
        result = action()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(token, result.stderr)
        self.assertEqual(self.controller_bytes(), before)
        return result


class Unbound(DeferredBindingCase):
    def test_awaiting_binding(self):
        """Runbook receipt reports awaiting binding without a runner file."""
        state = self.start()
        self.assertFalse(Path(self.target, RUNNER).exists())
        records = state['receipts']['runbook']['gate_commands']['commands']
        results = [invocation['result'] for command in records
                   for invocation in command['invocations']]
        self.assertTrue(results)
        self.assertEqual(set(results), {'interface-deferred'})
        expected = {'status': 'awaiting-binding', 'validation': 'interface-only',
                    'deferred': [{'path': RUNNER, 'step': 'step:1'}]}
        self.assertEqual(self.gate_status(), expected)
        plain = self.run_ctl('status').stdout
        lines = [line.removeprefix('gate commands: ') for line in plain.splitlines()
                 if line.startswith('gate commands: ')]
        self.assertEqual([json.loads(line) for line in lines], [expected])
        self.run_ctl('verify')

    def test_runner_unread(self):
        """The unbound runner is never read while Step 1 changes it."""
        self.start()
        self.create_runner(commit=False)
        runner = Path(self.target, RUNNER)
        # An unreadable runner would refuse any replay that opened it.
        runner.chmod(0)
        try:
            self.assertEqual(self.gate_status()['status'], 'awaiting-binding')
            self.run_ctl('verify')
            # The pre-mutation replay passes; only the command's own rule refuses.
            refused = self.run_ctl('config', 'set', 'audit.max_rounds', '7', expect=2)
            self.assertIn('config path is immutable', refused.stderr)
        finally:
            runner.chmod(0o644)
        runner.write_text(RUNNER_PROGRAM + '# changed during Step 1\n', encoding='utf-8')
        self.run_ctl('verify')


class Binding(DeferredBindingCase):
    def test_push_binds_blob(self):
        """Step 1's push binds the pushed blob and status reports current."""
        binding = self.to_bound()
        state = self.state()
        push = state['steps'][0]['receipts']['push']
        self.assertEqual(set(binding), {'step', 'starting_commit', 'push_head', 'paths',
                                        'gate_commands'})
        self.assertEqual(binding['step'], 'step:1')
        self.assertEqual(binding['starting_commit'], state['base'])
        self.assertEqual(binding['push_head'], push['head_commit'])
        blob = self.git('rev-parse', push['head_commit'] + ':' + RUNNER).stdout.strip()
        self.assertEqual(binding['paths'], [{
            'path': RUNNER, 'builder': 'build_parser', 'mode': '100644', 'blob': blob,
            'sha256': hashlib.sha256(RUNNER_PROGRAM.encode()).hexdigest()}])
        record = binding['gate_commands']
        self.assertEqual(record['artifact_sha256'],
                         state['receipts']['runbook']['sha256'])
        invocations = [invocation for command in record['commands']
                       for invocation in command['invocations']]
        self.assertEqual({item['result'] for item in invocations}, {'interface-valid'})
        self.assertEqual({item['cli']['sha256'] for item in invocations},
                         {binding['paths'][0]['sha256']})
        ledger = [json.loads(line) for line in
                  Path(self.target, '.hexaemeron/ledger.jsonl').read_text().splitlines()]
        pushed = [entry for entry in ledger if entry['event'] == 'done:push']
        self.assertEqual(pushed[-1]['data']['gate_binding'], binding)
        self.assertEqual(self.gate_status(), {'status': 'current', 'validation': 'interface-only'})
        self.run_ctl('verify')

    def test_executable_mode(self):
        """An executable runner binds its mode."""
        self.start()
        self.create_runner(commit=False)
        os.chmod(Path(self.target, RUNNER), 0o755)
        self.git('add', RUNNER)
        self.git('commit', '-q', '-m', 'Add an executable runner')
        self.implement_step_one()
        self.audit_step_one()
        self.push()
        binding = self.state()['steps'][0]['receipts']['push']['gate_binding']
        self.assertEqual(binding['paths'][0]['mode'], '100755')

    def test_no_deferred_row(self):
        """Marked run without a deferred row records no binding."""
        pinned = RUNNER + ' | build_parser | ' + hashlib.sha256(RUNNER_PROGRAM.encode()).hexdigest()
        self.start(rows=(pinned,), before_runbook=lambda: self.write(RUNNER, RUNNER_PROGRAM))
        self.assertEqual(self.gate_status()['status'], 'current')
        self.create_runner()
        self.implement_step_one()
        self.audit_step_one()
        self.push()
        self.assertNotIn('gate_binding', self.state()['steps'][0]['receipts']['push'])
        ledger = Path(self.target, '.hexaemeron/ledger.jsonl').read_text()
        self.assertNotIn('gate_binding', ledger)
        self.assertEqual(self.gate_status(), {'status': 'current', 'validation': 'interface-only'})
        self.run_ctl('verify')


class Refusal(DeferredBindingCase):
    def refuse_push(self, token):
        return self.assert_refused_unchanged(lambda: self.push(expect=1), token)

    def test_present_at_base(self):
        """Runner present at the starting commit refuses."""
        self.write(RUNNER, RUNNER_PROGRAM)
        self.git('add', RUNNER)
        self.git('commit', '-q', '-m', 'A runner that predates the run')
        self.start(before_runbook=lambda: os.remove(Path(self.target, RUNNER)))
        self.create_runner(RUNNER_PROGRAM + '# restored by Step 1\n')
        self.implement_step_one()
        self.audit_step_one()
        self.refuse_push('deferred-source-present-at-base')

    def test_absent_at_head(self):
        """Runner absent at the push head refuses then binds after a fix."""
        self.start()
        self.create_runner(commit=False)
        self.write('notes.md', 'Step 1 notes.\n')
        self.git('add', 'notes.md')
        self.git('commit', '-q', '-m', 'Step 1 without its runner')
        self.implement_step_one()
        self.audit_step_one()
        self.refuse_push('deferred-source-absent-at-head')
        self.git('add', RUNNER)
        self.git('commit', '-q', '-m', 'Commit the runner')
        self.push()
        self.assertIn('gate_binding', self.state()['steps'][0]['receipts']['push'])

    def refuse_irregular_entry(self, case):
        self.start()
        self.git('checkout', '-q', self.step_branch(1))
        target = Path(self.target, RUNNER)
        target.parent.mkdir(parents=True, exist_ok=True)
        if case == 'link':
            self.write('tests/real_runner.py', RUNNER_PROGRAM)
            os.symlink('real_runner.py', target)
            self.git('add', RUNNER, 'tests/real_runner.py')
        elif case == 'submodule':
            self.git('update-index', '--add', '--cacheinfo',
                     '160000,' + self.head() + ',' + RUNNER)
        else:
            self.write(RUNNER + '/inner.py', RUNNER_PROGRAM)
            self.git('add', RUNNER + '/inner.py')
        self.git('commit', '-q', '-m', 'A runner that is not a regular file')
        self.implement_step_one()
        self.audit_step_one()
        self.refuse_push('deferred-source-mode')

    def test_link(self):
        """Runner committed as a link refuses."""
        self.refuse_irregular_entry('link')

    def test_submodule(self):
        """Runner committed as a submodule refuses."""
        self.refuse_irregular_entry('submodule')

    def test_directory(self):
        """Runner committed as a directory refuses."""
        self.refuse_irregular_entry('directory')

    def test_worktree_mismatch(self):
        """Worktree copy differing from the pushed blob refuses."""
        self.to_push_boundary()
        runner = Path(self.target, RUNNER)
        runner.write_text(RUNNER_PROGRAM + '# uncommitted edit\n', encoding='utf-8')
        self.refuse_push('deferred-worktree-mismatch')
        runner.write_text(RUNNER_PROGRAM, encoding='utf-8')
        self.push()

    def test_linked_copy(self):
        """A linked worktree copy refuses through the no-follow read."""
        # A read that followed the link would compare the target's bytes and
        # report a mismatch; the no-follow read refuses the link itself.
        self.to_push_boundary()
        runner = Path(self.target, RUNNER)
        copy_path = Path(self.target, 'tests/copy_of_runner.py')
        copy_path.write_text(RUNNER_PROGRAM + '# linked copy\n', encoding='utf-8')
        runner.unlink()
        os.symlink('copy_of_runner.py', runner)
        result = self.refuse_push('gate binding refused: source-unavailable: ' + RUNNER)
        self.assertNotIn('deferred-worktree-mismatch', result.stderr)

    def test_parser_mismatch(self):
        """Runner that rejects its commands refuses with the adapter token."""
        self.to_push_boundary(RUNNER_PROGRAM.replace(
            '    parser.add_argument("--pattern", default="test_*.py", help="discovery pattern")\n', ''))
        self.refuse_push('gate binding refused: cli-arguments')

    def test_over_cap(self):
        """Runner over the source cap refuses."""
        self.to_push_boundary(RUNNER_PROGRAM + '#' * (2 * 1024 * 1024) + '\n')
        self.refuse_push('gate binding refused: source-not-bounded-regular')



class Verify(DeferredBindingCase):
    def to_step_two(self):
        """Bind at Step 1's push, then stand on Step 2's branch cut from it."""
        binding = self.to_bound()
        step_one = self.head()
        self.git('checkout', '-q', '-B', self.step_branch(2), step_one)
        return binding

    def test_later_edit(self):
        """Verify replays the binding and a later edit refuses as drift."""
        self.to_step_two()
        self.run_ctl('verify')
        runner = Path(self.target, RUNNER)
        runner.write_text(RUNNER_PROGRAM + '# edited by Step 2\n', encoding='utf-8')
        self.git('commit', '-q', '-am', 'Edit the bound runner')
        before = self.controller_bytes()
        refused = self.run_ctl('verify', expect=1)
        self.assertIn('registered-source-drift', refused.stderr)
        self.assertEqual(self.gate_status()['status'], 'stale-or-invalid')
        self.assert_refused_unchanged(
            lambda: self.run_ctl('done', 'implement', '--branch', self.step_branch(2),
                                 '--commit', self.head(), expect=1),
            'registered-source-drift')
        self.assertEqual(self.controller_bytes(), before)

    def test_digest_amendment(self):
        """A concrete digest amendment admits the later edit."""
        self.to_step_two()
        edited = RUNNER_PROGRAM + '# reviewed by an amendment\n'
        Path(self.target, RUNNER).write_text(edited, encoding='utf-8')
        self.git('commit', '-q', '-am', 'Edit the bound runner')
        self.run_ctl('verify', expect=1)
        row = RUNNER + ' | build_parser | ' + hashlib.sha256(edited.encode()).hexdigest()
        self.amend('Complete replacement Files: `' + RUNNER + '`.\n\n' + fence(row),
                   touched='Step 2.', verdicts='Step 2: entry holds; exit holds.')
        self.run_ctl('verify')
        state = self.state()
        latest = state['receipts']['runbook']['amendments'][-1]['gate_commands']
        clis = {invocation['cli']['sha256'] for command in latest['commands']
                for invocation in command['invocations']}
        self.assertEqual(clis, {hashlib.sha256(edited.encode()).hexdigest()})
        self.assertEqual(self.gate_status()['status'], 'current')

    def test_no_second_binding(self):
        """Later steps record no further binding."""
        binding = self.to_step_two()
        self.write('core.md', 'Step 2 work.\n')
        self.git('add', 'core.md')
        self.git('commit', '-q', '-m', 'Step 2 work')
        self.run_ctl('done', 'implement', '--branch', self.step_branch(2), '--commit', self.head())
        self.run_ctl('audit-round', '--findings', '0', *LINTS_CLEAN)
        self.run_ctl('done', 'audit')
        self.run_ctl('done', 'prose', '--files', '1',
                     '--skills', 'hexaemeron:imprimatur,hexaemeron:vulgate')
        self.push(2)
        state = self.state()
        self.assertNotIn('gate_binding', state['steps'][1]['receipts']['push'])
        self.assertEqual(state['steps'][0]['receipts']['push']['gate_binding'], binding)
        self.run_ctl('verify')


class Custody(DeferredBindingCase):
    """State and ledger must carry the same binding, in the shape recorded."""

    def rewrite_state(self, change):
        module = hexctl_module()
        path = Path(self.target, '.hexaemeron/state.json')
        state = json.loads(path.read_bytes())
        change(state)
        module.commit(self.target, state, 'fixture:forge-binding', {})

    def assert_verify_refuses(self, message):
        refused = self.run_ctl('verify', expect=1)
        self.assertIn(message, refused.stderr)
        self.assertEqual(self.gate_status()['status'], 'stale-or-invalid')

    def test_state_drop(self):
        """A binding dropped from state refuses."""
        self.to_bound()
        self.rewrite_state(lambda state: state['steps'][0]['receipts']['push'].pop('gate_binding'))
        self.assert_verify_refuses('gate binding disagrees with its immutable ledger record')

    def test_state_add(self):
        """A binding added to state without a ledger record refuses."""
        pinned = RUNNER + ' | build_parser | ' + hashlib.sha256(RUNNER_PROGRAM.encode()).hexdigest()
        self.to_push_boundary(rows=(pinned,), before_runbook=lambda: self.write(RUNNER, RUNNER_PROGRAM))
        self.push()
        forged = {'step': 'step:1', 'starting_commit': self.state()['base'],
                  'push_head': self.head(), 'paths': [], 'gate_commands': {}}
        self.rewrite_state(
            lambda state: state['steps'][0]['receipts']['push'].update(gate_binding=forged))
        self.assert_verify_refuses('gate binding disagrees with its immutable ledger record')

    def test_outside_step_one(self):
        """A binding outside Step 1's push receipt refuses."""
        binding = self.to_bound()

        def move(state):
            state['steps'][1]['receipts']['push'] = {'gate_binding': binding}
        self.rewrite_state(move)
        self.assert_verify_refuses("gate binding is recorded outside Step 1's push receipt")

    def forged_verification(self, change):
        """Change the binding in state and ledger alike, then verify directly."""
        module = hexctl_module()
        state = json.loads(Path(self.target, '.hexaemeron/state.json').read_bytes())
        entries = [json.loads(line) for line in
                   Path(self.target, '.hexaemeron/ledger.jsonl').read_text().splitlines()]
        binding = copy.deepcopy(state['steps'][0]['receipts']['push']['gate_binding'])
        phase = module.gate_phase(entries)
        change(binding, phase)
        state['steps'][0]['receipts']['push']['gate_binding'] = binding
        runbook = [entry['data'] for entry in entries if entry['event'] == 'done:runbook'][-1]
        amendments = [entry['data'] for entry in entries if entry['event'] == 'amend:runbook']
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.env), contextlib.redirect_stderr(stderr):
            try:
                module.verify_gate_commands(
                    self.target, state, entries[0], runbook, amendments,
                    binding_event={'gate_binding': binding}, phase=phase)
            except SystemExit as stopped:
                self.assertEqual(stopped.code, 1)
                return stderr.getvalue()
        return None

    def test_unforged(self):
        """The unforged binding verifies directly."""
        self.to_bound()
        self.assertIsNone(self.forged_verification(lambda binding, phase: None))

    def test_forged_shapes(self):
        """Forged binding shapes refuse."""
        self.to_bound()
        row = lambda binding: binding['paths'][0]
        cases = {
            'step': lambda b, p: b.update(step='step:2'),
            'extra-key': lambda b, p: b.update(note='x'),
            'starting-commit': lambda b, p: b.update(starting_commit='0' * 40),
            'push-head': lambda b, p: b.update(push_head='0' * 40),
            'no-paths': lambda b, p: b.update(paths=[]),
            'record-type': lambda b, p: b.update(gate_commands=[]),
            'row-key': lambda b, p: row(b).update(note='x'),
            'mode': lambda b, p: row(b).update(mode='120000'),
            'blob': lambda b, p: row(b).update(blob='z' * 40),
            'digest': lambda b, p: row(b).update(sha256='0' * 63),
            'builder-type': lambda b, p: row(b).update(builder=1),
            'duplicate': lambda b, p: b['paths'].append(dict(row(b))),
            'unsorted': lambda b, p: b['paths'].insert(0, dict(row(b), path='tests/z.py')),
            'too-many': lambda b, p: b['paths'].extend(
                dict(row(b), path=f'tests/z{index:02d}.py') for index in range(32)),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                message = self.forged_verification(change)
                self.assertIsNotNone(message)
                self.assertIn('gate binding record is malformed', message)

    def test_forged_records(self):
        """Forged binding records refuse."""
        self.to_bound()
        record = lambda binding: binding['gate_commands']
        invocation = lambda binding: record(binding)['commands'][0]['invocations'][0]
        cases = {
            'record-source': (lambda b, p: record(b).update(artifact_sha256='0' * 64),
                              'gate receipt source identity drift'),
            'record-unbound': (lambda b, p: invocation(b).update(result='interface-deferred'),
                               'gate binding record does not validate its bound runner'),
            'record-digest': (lambda b, p: invocation(b)['cli'].update(sha256='0' * 64),
                              'gate binding record does not validate its bound runner'),
            'phase-count': (lambda b, p: p.update(regions_before_binding=5),
                            'gate binding does not follow the runbook receipts'),
            'phase-paths': (lambda b, p: p.update(bindings={}),
                            'gate binding does not follow the runbook receipts'),
        }
        for name, (change, expected) in cases.items():
            with self.subTest(case=name):
                message = self.forged_verification(change)
                self.assertIsNotNone(message)
                self.assertIn(expected, message)

    def test_empty_binding(self):
        """An empty state binding refuses directly."""
        self.to_bound()
        module = hexctl_module()
        state = json.loads(Path(self.target, '.hexaemeron/state.json').read_bytes())
        state['steps'][0]['receipts']['push']['gate_binding'] = None
        initial = json.loads(
            Path(self.target, '.hexaemeron/ledger.jsonl').read_text().splitlines()[0])
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.env), contextlib.redirect_stderr(stderr), \
                self.assertRaises(SystemExit):
            module.verify_gate_commands(self.target, state, initial, {}, [], binding_event={})
        self.assertIn('gate binding record is malformed', stderr.getvalue())

    def test_ledger_only(self):
        """A ledger binding without a state binding refuses directly."""
        self.to_bound()
        module = hexctl_module()
        state = json.loads(Path(self.target, '.hexaemeron/state.json').read_bytes())
        entries = [json.loads(line) for line in
                   Path(self.target, '.hexaemeron/ledger.jsonl').read_text().splitlines()]
        state['steps'][0]['receipts']['push'].pop('gate_binding')
        runbook = [entry['data'] for entry in entries if entry['event'] == 'done:runbook'][-1]
        stderr = io.StringIO()
        for binding_event in ({}, None):
            with self.subTest(binding_event=binding_event), \
                    mock.patch.dict(os.environ, self.env), contextlib.redirect_stderr(stderr), \
                    self.assertRaises(SystemExit):
                # The phase still records the ledger's binding.
                module.verify_gate_commands(
                    self.target, state, entries[0], runbook, [],
                    binding_event=binding_event, phase=module.gate_phase(entries))
        self.assertIn('gate binding disagrees with its immutable ledger record', stderr.getvalue())


class Readers(DeferredBindingCase):
    """The Git readers behind the binding, fed answers real Git never gives."""

    def refusal(self, call, answers):
        module = hexctl_module()
        replies = iter(answers)
        stderr = io.StringIO()
        with mock.patch.object(module, '_guard_native_git', lambda *args: next(replies)), \
                contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            call(module)
        return stderr.getvalue()

    def test_tree_entries(self):
        """Tree entries Git would never print refuse."""
        oid = 'a' * 40
        for answer in (b'100644 blob ' + oid.encode() + b'\ttests/other.py\0',
                       b'100644 blob ' + oid.encode() + b' tests/run_tests.py\0',
                       b'100644 blob short\t' + RUNNER.encode() + b'\0',
                       (b'100644 blob ' + oid.encode() + b'\t' + RUNNER.encode() + b'\0') * 2):
            with self.subTest(answer=answer):
                message = self.refusal(
                    lambda module: module._gate_binding_tree_entry('.', 'b' * 40, RUNNER),
                    [answer])
                self.assertIn('gate binding refused: deferred-source-unreadable', message)

    def test_blob_identity(self):
        """Blob sizes and bytes must agree with the object id."""
        data = RUNNER_PROGRAM.encode()
        oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        module = hexctl_module()
        header = b'blob ' + str(len(data)).encode() + b'\0'
        for object_id in (oid, hashlib.sha256(header + data).hexdigest()):
            with self.subTest(object_id=object_id):
                replies = iter([str(len(data)).encode() + b'\n', data])
                with mock.patch.object(module, '_guard_native_git',
                                       lambda *args: next(replies)):
                    self.assertEqual(module._gate_binding_blob('.', object_id, 1024), data)
        cases = {
            'malformed-size': ([b'not-a-size\n'], oid, 1024, 'deferred-source-unreadable'),
            'over-cap': ([str(len(data)).encode()], oid, len(data) - 1,
                         'source-not-bounded-regular'),
            'short-read': ([str(len(data)).encode(), data[:-1]], oid, 1024,
                           'deferred-source-unreadable'),
            'wrong-object': ([str(len(data)).encode(), data], '0' * 40, 1024,
                             'deferred-source-unreadable'),
            'wrong-algorithm': ([str(len(data)).encode(), data], '0' * 64, 1024,
                                'deferred-source-unreadable'),
        }
        for name, (answers, object_id, cap, token) in cases.items():
            with self.subTest(case=name):
                message = self.refusal(
                    lambda module: module._gate_binding_blob('.', object_id, cap), answers)
                self.assertIn('gate binding refused: ' + token, message)

    def test_start_commit(self):
        """A starting commit that is not a full SHA refuses."""
        self.to_push_boundary()
        module = hexctl_module()
        state = json.loads(Path(self.target, '.hexaemeron/state.json').read_bytes())
        state['base'] = 'main'
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.env), contextlib.redirect_stderr(stderr), \
                self.assertRaises(SystemExit):
            module.capture_gate_binding(self.target, state, state['steps'][0], self.head())
        self.assertIn('gate binding refused: deferred-starting-commit-unknown', stderr.getvalue())

    def test_phase_refusal(self):
        """A phase the runbook cannot hold refuses the binding."""
        self.to_push_boundary()
        module = hexctl_module()
        state = json.loads(Path(self.target, '.hexaemeron/state.json').read_bytes())
        phase = {'regions': 5, 'regions_before_implementation': 5, 'bindings': {},
                 'regions_before_binding': None}
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.env), \
                mock.patch.object(module, 'current_gate_phase', lambda base_dir: phase), \
                contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.capture_gate_binding(self.target, state, state['steps'][0], self.head())
        self.assertIn('gate binding refused: deferred-phase-invalid', stderr.getvalue())

    def test_object_kind(self):
        """A tree entry of another object kind refuses by mode."""
        self.to_push_boundary()
        module = hexctl_module()
        state = json.loads(Path(self.target, '.hexaemeron/state.json').read_bytes())
        head = self.head()
        entries = {state['base']: None, head: ('100644', 'commit', 'c' * 40)}
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, self.env), \
                mock.patch.object(module, '_gate_binding_tree_entry',
                                  lambda base_dir, commit, path: entries[commit]), \
                contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.capture_gate_binding(self.target, state, state['steps'][0], head)
        self.assertIn('gate binding refused: deferred-source-mode', stderr.getvalue())

    def test_malformed_ledger(self):
        """A malformed ledger binding refuses the phase read."""
        module = hexctl_module()
        entries = [{'event': 'done:push', 'data': {'step': 1, 'gate_binding': {'paths': {}}}}]
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module.gate_phase(entries)
        self.assertIn('gate binding ledger record is malformed', stderr.getvalue())

    def test_restore_branch(self):
        """The restore branch follows the binding."""
        module = hexctl_module()
        state = {'run_branch': 'fiat/run', 'steps': [
            {'n': 1, 'receipts': {'implement': {'branch': 'fiat/run-step-1-a'},
                                  'push': {'gate_binding': {}}}},
            {'n': 2, 'receipts': {'implement': {'branch': 'fiat/run-step-2-b'}}},
            {'n': 3, 'receipts': {}},
        ]}
        self.assertEqual(module._checkpoint_restore_branch(state), 'fiat/run-step-2-b')
        unbound = copy.deepcopy(state)
        unbound['steps'][0]['receipts']['push'].pop('gate_binding')
        self.assertEqual(module._checkpoint_restore_branch(unbound), 'fiat/run')
        for branch in (None, 'bad..branch'):
            with self.subTest(branch=branch):
                broken = copy.deepcopy(state)
                broken['steps'][1]['receipts'] = {}
                if branch is None:
                    broken['steps'][0]['receipts'].pop('implement')
                else:
                    broken['steps'][0]['receipts']['implement']['branch'] = branch
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    module._checkpoint_restore_branch(broken)


class Amend(DeferredBindingCase):
    SECOND_ROW = OTHER_RUNNER + ' | build_parser | step:1'

    def test_before_step_one(self):
        """A deferred row may be added before Step 1's implementation receipt."""
        self.start()
        self.amend('Complete replacement Files: `' + RUNNER + '`.\n\n'
                   + fence(DEFERRED_ROW, self.SECOND_ROW))
        self.assertEqual(self.gate_status()['deferred'],
                         [{'path': OTHER_RUNNER, 'step': 'step:1'},
                          {'path': RUNNER, 'step': 'step:1'}])
        # Before Step 1's implementation receipt the new path must be absent.
        self.write(OTHER_RUNNER, RUNNER_PROGRAM)
        self.assert_refused_unchanged(
            lambda: self.amend('Complete replacement Files: `' + RUNNER + '` again.\n\n'
                               + fence(DEFERRED_ROW, self.SECOND_ROW), expect=1,
                               name='second.md'),
            'deferred-source-present')

    def test_repeat_only(self):
        """After Step 1's implementation receipt only a byte-identical repeat is admitted."""
        self.start()
        self.create_runner()
        self.implement_step_one()
        self.assert_refused_unchanged(
            lambda: self.amend('Complete replacement Files: `' + RUNNER + '`.\n\n'
                               + fence(DEFERRED_ROW, self.SECOND_ROW), expect=1),
            'deferred-row-after-step-start')
        # The runner exists now and stays unread by the repeated row.
        self.amend('Complete replacement Files: `' + RUNNER + '`.\n\n' + fence(DEFERRED_ROW),
                   name='repeat.md')
        self.assertEqual(self.gate_status()['status'], 'awaiting-binding')

    def test_after_binding(self):
        """After binding the deferred row cannot return."""
        self.to_bound()
        self.assert_refused_unchanged(
            lambda: self.amend('Complete replacement Files: `' + RUNNER + '`.\n\n'
                               + fence(DEFERRED_ROW), touched='Step 2.',
                               verdicts='Step 2: entry holds; exit holds.', expect=1),
            'deferred-row-after-binding')

    def test_amended_prefix(self):
        """A binding after an amendment replays that amendment's prefix."""
        self.start()
        self.amend('Complete replacement Files: `' + RUNNER + '` and notes.')
        self.create_runner()
        self.implement_step_one()
        self.audit_step_one()
        self.push()
        state = self.state()
        binding = state['steps'][0]['receipts']['push']['gate_binding']
        self.assertEqual(binding['gate_commands']['artifact_sha256'],
                         state['receipts']['runbook']['amendments'][-1]['new_sha256'])
        self.run_ctl('verify')


class Counts(DeferredBindingCase):
    def test_receipt_counts(self):
        """Phase counts come from receipts in ledger order."""
        module = hexctl_module()
        binding = {'paths': [{'path': RUNNER, 'sha256': 'a' * 64}]}
        entries = [
            {'event': 'init', 'data': {}},
            {'event': 'done:runbook', 'data': {}},
            {'event': 'amend:runbook', 'data': {}},
            {'event': 'done:implement', 'data': {'step': 1}},
            {'event': 'amend:runbook', 'data': {}},
            {'event': 'done:implement', 'data': {'step': 1}},
            {'event': 'done:push', 'data': {'step': 1, 'gate_binding': binding}},
            {'event': 'amend:runbook', 'data': {}},
            {'event': 'done:push', 'data': {'step': 2}},
        ]
        self.assertEqual(module.gate_phase(entries), {
            'regions': 4, 'regions_before_implementation': 2,
            'bindings': {RUNNER: 'a' * 64}, 'regions_before_binding': 3})
        self.assertEqual(module.gate_phase(entries, 3), {
            'regions': 2, 'regions_before_implementation': None,
            'bindings': {}, 'regions_before_binding': None})
        self.assertEqual(module.gate_phase_keywords(module.gate_phase(entries, 3)), {})
        self.assertEqual(
            module.gate_phase_keywords(module.gate_phase(entries), require_absent=False),
            {'require_absent': False, 'regions_before_implementation': 2,
             'bindings': {RUNNER: 'a' * 64}, 'regions_before_binding': 3})

    def test_late_row(self):
        """A late deferred row refuses although a heading count would admit it."""
        # Two regions precede Step 1's implementation receipt. The candidate
        # holds four headings, so a count taken from it would admit the row.
        self.start()
        self.amend('Complete replacement Files: `' + RUNNER + '` and notes.')
        self.create_runner()
        self.implement_step_one()
        self.amend('Complete replacement Files: `' + RUNNER + '` and a log.', name='second.md')
        self.assert_refused_unchanged(
            lambda: self.amend('Complete replacement Files: `' + RUNNER + '`.\n\n'
                               + fence(DEFERRED_ROW, OTHER_RUNNER + ' | build_parser | step:1'),
                               expect=1, name='third.md'),
            'deferred-row-after-step-start')

    def test_loose_heading(self):
        """A heading the adapter does not count leaves a run without deferred rows unblocked."""
        pinned = RUNNER + ' | build_parser | ' + hashlib.sha256(RUNNER_PROGRAM.encode()).hexdigest()
        self.start(rows=(pinned,), before_runbook=lambda: self.write(RUNNER, RUNNER_PROGRAM))
        candidate = self.write(
            '.hexaemeron/loose.md',
            self.runbook_path.read_text(encoding='utf-8') + self.runbook_amendment(
                verdicts='Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.',
                what='Complete replacement Files: `' + RUNNER + '` and notes.',
                touched='Step 1.').replace('### Amendment', '###  Amendment'))
        self.run_ctl('amend', 'runbook', '--artifact', candidate)
        self.create_runner()
        self.implement_step_one()
        # Two receipted regions now precede the implementation receipt.
        self.run_ctl('verify')
        self.audit_step_one()
        self.push()
        self.assertEqual(self.gate_status(), {'status': 'current', 'validation': 'interface-only'})


class Checkpoint(DeferredBindingCase):
    def direct_environment(self):
        environment = dict(self.env)
        environment['FAKE_GIT_REFS'] = json.dumps(self.fake_refs)
        environment['FAKE_GIT_PARENTS'] = json.dumps(self.fake_parents)
        environment['FAKE_GH_PRS'] = json.dumps(self.fake_prs)
        return environment

    def hexctl(self, worktree, *args, expect=0):
        result = subprocess.run([sys.executable, HEXCTL, *args], cwd=worktree,
                                capture_output=True, text=True, env=self.direct_environment())
        self.assertEqual(result.returncode, expect, result.stderr)
        return result

    def export_and_restore(self):
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        root = Path(os.path.realpath(home.name))
        capsule = root / 'capsule'
        payload = json.loads(self.run_ctl('checkpoint', 'export', '--out', str(capsule)).stdout)
        origin = root / 'origin'
        subprocess.run(['git', 'clone', '-q', self.dir, str(origin)], check=True,
                       capture_output=True)
        manifest = json.loads((capsule / 'MANIFEST.json').read_bytes())
        for ref in manifest['boundary']['refs']:
            if ref == 'main' or re.fullmatch(r'[0-9a-f]{40}', ref):
                continue
            subprocess.run(['git', 'branch', ref, 'origin/' + ref], cwd=origin, check=True,
                           capture_output=True)
        restored = subprocess.run(
            [sys.executable, HEXCTL, '--dir', str(origin), 'checkpoint', 'restore',
             '--from', str(capsule), '--manifest-sha256', payload['manifest_sha256']],
            capture_output=True, text=True, env=self.direct_environment())
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual(json.loads(restored.stdout)['verify'], 'ok')
        worktree = Path((origin / '.hexaemeron' / 'worktree').read_text(encoding='utf-8').strip())
        return worktree

    def test_after_binding(self):
        """Restore after binding replays the binding on the step branch."""
        binding = self.to_bound()
        worktree = self.export_and_restore()
        state = json.loads((worktree / '.hexaemeron/state.json').read_bytes())
        self.assertEqual(state['steps'][0]['receipts']['push']['gate_binding'], binding)
        ledger = (worktree / '.hexaemeron/ledger.jsonl').read_text().splitlines()
        pushed = [json.loads(line) for line in ledger if '"done:push"' in line]
        self.assertEqual(pushed[-1]['data']['gate_binding'], binding)
        branch = subprocess.run(['git', 'symbolic-ref', '--short', 'HEAD'], cwd=worktree,
                                capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(branch, self.step_branch(1))
        self.hexctl(worktree, 'verify')
        status = json.loads(self.hexctl(worktree, 'status', '--field', 'gate_command_status').stdout)
        self.assertEqual(status, {'status': 'current', 'validation': 'interface-only'})
        (worktree / RUNNER).write_text(RUNNER_PROGRAM + '# edited after restore\n',
                                       encoding='utf-8')
        refused = self.hexctl(worktree, 'verify', expect=1)
        self.assertIn('registered-source-drift', refused.stderr)

    def test_before_binding(self):
        """Restore before binding replays the row as unbound."""
        self.start()
        self.create_runner()
        self.implement_step_one()
        self.record_legacy_config('audit.max_rounds', 1)
        self.run_ctl('audit-round', '--findings', '1', *LINTS_CLEAN)
        self.assertEqual(self.next_json()['do'], 'audit-verdict')
        worktree = self.export_and_restore()
        state = json.loads((worktree / '.hexaemeron/state.json').read_bytes())
        self.assertNotIn('push', state['steps'][0]['receipts'])
        branch = subprocess.run(['git', 'symbolic-ref', '--short', 'HEAD'], cwd=worktree,
                                capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(branch, state['run_branch'])
        self.assertFalse((worktree / RUNNER).exists())
        self.hexctl(worktree, 'verify')
        status = json.loads(self.hexctl(worktree, 'status', '--field', 'gate_command_status').stdout)
        self.assertEqual(status['status'], 'awaiting-binding')


class Criteria(DeferredBindingCase):
    def test_admission_phase(self):
        """Admission replays under the phase that captured it."""
        self.start(criteria=True)
        admission = self.state()['receipts']['runbook']['success_criteria']
        results = {invocation['result'] for command in admission['gate_commands']['commands']
                   for invocation in command['invocations']}
        self.assertEqual(results, {'interface-deferred'})
        self.create_runner()
        # The runner exists during Step 1; the admission replay never needs it absent.
        self.run_ctl('verify')
        self.implement_step_one()
        # A runbook amendment after the implementation receipt re-admits the criteria.
        self.amend('Complete replacement Files: `' + RUNNER + '` and notes.')
        self.run_ctl('verify')
        self.audit_step_one()
        self.push()
        # The admission predates the binding and replays without it.
        self.run_ctl('verify')
        self.git('checkout', '-q', '-B', self.step_branch(2), self.head())
        self.amend('Complete replacement Files: `' + RUNNER + '` and a log.',
                   touched='Step 2.', verdicts='Step 2: entry holds; exit holds.',
                   name='after-binding.md')
        self.run_ctl('verify')
        admission = self.state()['receipts']['runbook']['success_criteria']
        results = {invocation['result'] for command in admission['gate_commands']['commands']
                   for invocation in command['invocations']}
        self.assertEqual(results, {'interface-valid'})

    def amend_study(self, touched, verdicts, name):
        candidate = self.write('.hexaemeron/' + name, Path(self.target, '.hexaemeron/study.md').read_text(
            encoding='utf-8') + (
                '\n### Amendment -- 2026-09-21\n\n'
                '**What changed.** Record the reviewed runner.\n\n'
                '**Why.** Keep the source receipt current.\n\n'
                f'**Steps touched.** {touched}\n\n'
                f'**Still holding.** {verdicts}\n'))
        self.run_ctl('amend', 'study', '--artifact', candidate)

    def test_study_amendments(self):
        """Study amendments readmit under the current phase."""
        self.start(criteria=True)
        self.create_runner()
        # The runbook bytes are unchanged, so a present runner does not refuse.
        self.amend_study('Step 1.', 'Step 1: entry holds; exit holds. '
                         'Step 2: entry holds; exit holds.', 'study-before.md')
        self.run_ctl('verify')
        self.implement_step_one()
        self.audit_step_one()
        self.push()
        self.git('checkout', '-q', '-B', self.step_branch(2), self.head())
        self.amend_study('Step 2.', 'Step 2: entry holds; exit holds.', 'study-after.md')
        self.run_ctl('verify')
        admission = hexctl_module().success_criteria_admission(self.state())
        results = {invocation['result'] for command in admission['gate_commands']['commands']
                   for invocation in command['invocations']}
        self.assertEqual(results, {'interface-valid'})

    def test_run_exit(self):
        """`run-exit` replays the admission under its recorded phase."""
        self.start(criteria=True)
        self.create_runner()
        self.implement_step_one()
        self.audit_step_one()
        self.push()
        branch = self.step_branch(2)
        self.git('checkout', '-q', '-B', branch, self.head())
        self.amend('Complete replacement Files: `' + RUNNER + '` and a log.',
                   touched='Step 2.', verdicts='Step 2: entry holds; exit holds.')
        head = self.head()
        self.fake_refs[branch] = head
        before = self.controller_bytes()
        refused = self.run_ctl('run-exit', '--criterion', 'runner-exit', expect=1)
        # The admission replayed; execution then refuses the local runner.
        self.assertNotIn('admission is stale', refused.stderr)
        self.assertIn('run-exit refused', refused.stderr)
        self.assertEqual(self.controller_bytes(), before)


class Legacy(DeferredBindingCase):
    def test_unmarked_run(self):
        """A run without the gate marker is untouched."""
        self.to_push_boundary(legacy=True)
        self.assertEqual(self.gate_status(), {'status': 'legacy', 'validation': 'not-recorded'})
        self.push()
        state = self.state()
        self.assertNotIn('gate_commands', state['contracts'])
        self.assertNotIn('gate_binding', state['steps'][0]['receipts']['push'])
        self.assertEqual(self.gate_status(), {'status': 'legacy', 'validation': 'not-recorded'})
        self.run_ctl('verify')

    def test_released_adapter(self):
        """The released adapter refuses a deferred row."""
        root = Path(__file__).resolve().parents[3]
        source = subprocess.run(
            ['git', '-C', str(root), 'cat-file', 'blob',
             'e992a54b4e3e4671bae98b448d57690de8dfa044:'
             'plugins/hexaemeron/skills/protasis/scripts/gate_commands.py'],
            stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=60).stdout
        self.assertEqual(hashlib.sha256(source).hexdigest(),
                         '14a857dc44ce43d7a3771a2125b92f86435e39ab8ba2b027ef02b4f36ca48bad')
        path = Path(self.dir, 'released', 'gate_commands.py')
        path.parent.mkdir()
        path.write_bytes(source)
        spec = importlib.util.spec_from_file_location('deferred_binding_released_gate', path)
        released = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(released)
        with self.assertRaises(released.Refusal) as refused:
            released.validate(Path(self.dir).resolve(), runbook_text().encode())
        self.assertEqual(str(refused.exception), 'invalid-command-interfaces')


if __name__ == '__main__':
    unittest.main()
