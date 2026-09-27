"""Deferred step:1 registrations: grammar, absence, binding, placement and replay.

The module is self-contained so the skills#1944 conformance resolver can load
and run it as one unit. Released adapters are read from Git at the commits
that shipped them and checked by digest before any comparison.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = 'plugins/hexaemeron/skills/protasis/scripts/gate_commands.py'
PROTASIS = 'plugins/hexaemeron/skills/protasis/scripts/protasis.py'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gates = load(ROOT / ADAPTER, 'deferred_registration_gate')

RUNNER = 'tests/run_tests.py'
RUNNER_PROGRAM = '''import argparse


def build_parser():
    parser = argparse.ArgumentParser(description="Run the fixture suite.")
    parser.add_argument("--elenchus-report", help="write a report to this fresh path")
    parser.add_argument("--pattern", default="test_*.py", help="discovery pattern")
    return parser
'''
LOCAL_CLI = 'scripts/verify.py'
LOCAL_PROGRAM = '''import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--count', type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    return args
'''
STARTING_COMMIT = 'e992a54b4e3e4671bae98b448d57690de8dfa044'
# Each admitted released adapter, with the commit that shipped it.
RELEASED = (
    (STARTING_COMMIT, '14a857dc44ce43d7a3771a2125b92f86435e39ab8ba2b027ef02b4f36ca48bad'),
    ('6f4312c3ba706c1df88f535967d2d59e184c1f79',
     '6f50cd844a3543aa7ef05fc6631c72ba2fd91aab44ad3f06d62bb4f7312682de'),
)
# Hexaemeron 1.6.72 to 1.6.78; carried forward, never admitted here.
UNADMITTED = 'ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119'
ADMITTED = frozenset({
    '18eb52e7e6bc741bd2c80c55838de74831777ea0833147570963c10e0904c093',
    'c2d14b0f262ecde17f679a73a462cd2ed0f4305a54528e93e375f2b36514bbc6',
    '00d4c9f2a0905ea65d56a3ddca9a429c9a20d464d9b66f69098a954b5e7c37b0',
    'd7e49768547fe0c4673c8204d3392c57e60824448fac5bfe8a5bdf4ab5c1bef4',
    '3549ce4afff9cdbd3f8ba04beece3eb17d5cb4f51d954f71dd1d50733c237b0c',
    *(digest for _, digest in RELEASED),
})
REPORT = '.hexaemeron/reports/step-1-guard.json'
STEP_ONE = ('## Step 1: Scaffold\n\n**Goal.** Add the runner.\n\n'
            '**Exit.** `python3 ' + RUNNER + ' --pattern test_core.py`\n\n'
            '**Tests.** Elenchus command: `python3 ' + RUNNER + ' --elenchus-report {report}`; '
            'format: `unittest-json-v1`; report file: `' + REPORT + '`.\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fence(*rows):
    return ('```command-interfaces\nschema | protasis-command-interfaces/v1\n'
            + ''.join(row + '\n' for row in rows) + '```\n')


def deferred_row(path=RUNNER, builder='build_parser'):
    return path + ' | ' + builder + ' | step:1'


def amendment(*rows, date='2026-09-27'):
    return ('\n### Amendment -- ' + date + '\n\n**What changed.** Replace the registration set.\n\n'
            + fence(*rows) + '\n**Why.** Fixture.\n\n**Steps touched.** Step 1.\n\n'
            '**Still holding.** Step 1: entry holds; exit holds.\n')


def book(baseline=(deferred_row(),), *amendments):
    """A runbook whose baseline fence holds ``baseline`` rows, then each amendment."""
    return (fence(*baseline) + '\n' + STEP_ONE + ''.join(amendments)).encode()


def results(result):
    return [invocation['result'] for command in result['commands']
            for invocation in command.get('invocations', [])]


def released_adapter(commit, expected, directory):
    """Read one released adapter from Git and load it only after its digest matches."""
    blob = subprocess.run(['git', '-C', str(ROOT), 'cat-file', 'blob', commit + ':' + ADAPTER],
                          stdin=subprocess.DEVNULL, capture_output=True, check=True,
                          timeout=60).stdout
    if sha(blob) != expected:
        raise AssertionError('released adapter at ' + commit + ' is not ' + expected)
    path = Path(directory) / ('released-' + expected[:12]) / 'gate_commands.py'
    path.parent.mkdir(parents=True)
    path.write_bytes(blob)
    return load(path, 'deferred_registration_released_' + expected[:12])


class Target(unittest.TestCase):
    """A disposable target root with no runner."""

    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix='deferred-gate-')
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name).resolve()

    def write_runner(self, text=RUNNER_PROGRAM):
        path = self.root / RUNNER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return sha(text.encode())

    def refusal(self, operation):
        with self.assertRaises(gates.Refusal) as caught:
            operation()
        return str(caught.exception)

    def spy(self):
        return mock.patch.object(gates, 'read_source', wraps=gates.read_source)

    def assert_runner_unread(self, spy):
        self.assertNotIn(RUNNER, [call.args[1] for call in spy.call_args_list])


class DeferredRowGrammarTests(Target):
    def test_step_one_is_the_only_deferred_value(self):
        self.assertEqual(gates.declared_interfaces(
            'schema | protasis-command-interfaces/v1\n' + deferred_row() + '\n'),
            {RUNNER: ('build_parser', 'step:1')})
        for value in ('step:2', 'step:0', 'step:01', 'step:', 'step:1x', 'step:1 '):
            with self.subTest(value=value):
                book_bytes = book((RUNNER + ' | build_parser | ' + value,))
                self.assertEqual(self.refusal(lambda: gates.validate(self.root, book_bytes)),
                                 'deferred-step-unsupported')
        for value in ('Step:1', 'step 1', 'STEP:1', '1'):
            with self.subTest(value=value):
                book_bytes = book((RUNNER + ' | build_parser | ' + value,))
                self.assertEqual(self.refusal(lambda: gates.validate(self.root, book_bytes)),
                                 'invalid-command-interfaces')

    def test_escaping_paths_overrides_and_bounds_refuse_for_deferred_rows(self):
        cases = {
            '/tests/run_tests.py': 'unsafe-registered-path',
            './run_tests.py': 'unsafe-registered-path',
            'tests/../run_tests.py': 'unsafe-registered-path',
            'tests//run_tests.py': 'unsafe-registered-path',
            '.git/run_tests.py': 'unsafe-registered-path',
            'tests/.GIT/run_tests.py': 'unsafe-registered-path',
            'tests\\run_tests.py': 'invalid-command-interfaces',
            'tests/run_tests.sh': 'invalid-command-interfaces',
            'plugins/hexaemeron/tests/run_tests.py': 'duplicate-command-interface',
            'scripts/RUN_CHECKS.py': 'duplicate-command-interface',
        }
        for path, reason in cases.items():
            with self.subTest(path=path):
                data = book((deferred_row(path),))
                self.assertEqual(self.refusal(lambda: gates.validate(self.root, data)), reason)
        twice = book((deferred_row(), deferred_row('TESTS/run_tests.py')))
        self.assertEqual(self.refusal(lambda: gates.validate(self.root, twice)),
                         'duplicate-command-interface')
        many = book(tuple(deferred_row('tests/run_' + str(n) + '.py') for n in range(33)))
        self.assertEqual(self.refusal(lambda: gates.validate(self.root, many)),
                         'command-interface-bound')


class AbsentPathWalkTests(Target):
    def test_missing_component_or_leaf_is_absent_and_never_read(self):
        with self.spy() as spy:
            result = gates.validate(self.root, book())
        self.assertEqual(results(result), ['interface-deferred', 'interface-deferred'])
        self.assert_runner_unread(spy)
        (self.root / 'tests').mkdir()
        with self.spy() as spy:
            self.assertEqual(gates.validate(self.root, book()), result)
        self.assert_runner_unread(spy)

    def test_linked_or_non_directory_parent_is_unsafe(self):
        elsewhere = self.root / 'elsewhere'
        elsewhere.mkdir()
        (self.root / 'tests').symlink_to(elsewhere)
        self.assertEqual(self.refusal(lambda: gates.validate(self.root, book())),
                         'deferred-path-unsafe')
        (self.root / 'tests').unlink()
        (self.root / 'tests').symlink_to(self.root / 'missing')
        self.assertEqual(self.refusal(lambda: gates.validate(self.root, book())),
                         'deferred-path-unsafe')
        (self.root / 'tests').unlink()
        (self.root / 'tests').write_text('not a directory\n')
        self.assertEqual(self.refusal(lambda: gates.validate(self.root, book())),
                         'deferred-path-unsafe')

    def test_parent_replaced_between_lstat_and_open_is_unsafe(self):
        (self.root / 'tests').mkdir()
        real = os.fstat

        def shifted(descriptor):
            values = list(real(descriptor))
            values[stat.ST_INO] += 1
            return os.stat_result(values)

        with mock.patch.object(gates.os, 'fstat', shifted):
            reason = self.refusal(lambda: gates.require_deferred_absent(self.root, RUNNER))
        self.assertEqual(reason, 'deferred-path-unsafe')

    def test_existing_leaf_of_each_type_is_present(self):
        (self.root / 'tests').mkdir()
        leaf = self.root / RUNNER

        def regular():
            leaf.write_text(RUNNER_PROGRAM)

        def directory():
            leaf.mkdir()

        def link():
            leaf.symlink_to(self.root / 'tests')

        def dangling():
            leaf.symlink_to(self.root / 'missing.py')

        def fifo():
            os.mkfifo(leaf)

        def unix_socket():
            # Bind under a short name, then move it: AF_UNIX paths stop near 104 bytes.
            short = Path(tempfile.mkdtemp(prefix='s-'))
            self.addCleanup(shutil.rmtree, short, ignore_errors=True)
            server = socket.socket(socket.AF_UNIX)
            self.addCleanup(server.close)
            server.bind(str(short / 's'))
            os.rename(short / 's', leaf)
            self.assertTrue(stat.S_ISSOCK(os.lstat(leaf).st_mode))

        for make in (regular, directory, link, dangling, fifo, unix_socket):
            with self.subTest(kind=make.__name__):
                make()
                with self.spy() as spy:
                    self.assertEqual(self.refusal(lambda: gates.validate(self.root, book())),
                                     'deferred-source-present')
                self.assert_runner_unread(spy)
                if leaf.is_dir() and not leaf.is_symlink():
                    leaf.rmdir()
                else:
                    leaf.unlink()

    def test_absence_is_required_only_when_the_caller_asks(self):
        self.write_runner()
        self.assertEqual(self.refusal(lambda: gates.validate(self.root, book())),
                         'deferred-source-present')
        with self.spy() as spy:
            result = gates.validate(self.root, book(), require_absent=False)
        self.assertEqual(results(result), ['interface-deferred', 'interface-deferred'])
        self.assert_runner_unread(spy)
        for value in (0, 1, None, 'yes'):
            with self.subTest(value=value):
                self.assertEqual(
                    self.refusal(lambda: gates.validate(self.root, book(), require_absent=value)),
                    'deferred-phase-invalid')

    def test_gate_root_cli_applies_the_absence_rule(self):
        runbook = self.root / 'runbook.md'
        runbook.write_bytes(book())

        def gate_findings():
            completed = subprocess.run(
                [sys.executable, str(ROOT / PROTASIS), str(runbook), '--gate-root', str(self.root),
                 '--format', 'json'],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120,
                env={**os.environ, 'NO_COLOR': '1', 'FORCE_COLOR': ''}, check=False)
            return [item['message'] for item in json.loads(completed.stdout) if item['code'] == 'P008']

        self.assertEqual(gate_findings(), [])
        self.write_runner()
        self.assertEqual(gate_findings(), ['deferred-source-present'])


class UnboundCommandTests(Target):
    def test_unbound_invocations_record_the_deferred_result_without_reading(self):
        loop = ('for file in test_a.py test_b.py; do python3 ' + RUNNER
                + ' --pattern "$file"; done')
        data = fence(deferred_row()) + '\n' + STEP_ONE.replace(
            '**Exit.** `python3 ' + RUNNER + ' --pattern test_core.py`',
            '**Exit.** `' + loop + '`')
        with self.spy() as spy:
            result = gates.validate(self.root, data.encode())
        self.assert_runner_unread(spy)
        invocations = [invocation for command in result['commands']
                       for invocation in command['invocations']]
        self.assertEqual(len(invocations), 3)
        deferred = {'path': RUNNER, 'deferred': 'step:1'}
        for invocation in invocations:
            self.assertEqual(set(invocation), {'argv', 'execution_argv', 'cli', 'result'})
            self.assertEqual(invocation['cli'], deferred)
            self.assertEqual(invocation['result'], 'interface-deferred')
        self.assertEqual([item['argv'][-1] for item in invocations[:2]], ['test_a.py', 'test_b.py'])
        report = invocations[2]
        self.assertEqual(report['argv'][-1], '{report}')
        self.assertEqual(report['execution_argv'][-1], str(self.root / REPORT))
        self.assertEqual(result['schema'], 'protasis-gate-commands/v1')
        self.assertIs(result['operation_ran'], False)
        self.assertEqual(set(result), {'schema', 'artifact_sha256', 'source_root',
                                       'adapter_sha256', 'commands', 'operation_ran'})

    def test_unbound_commands_still_pass_every_other_check(self):
        registrations = {RUNNER: ('build_parser', 'step:1')}
        contract = {'format': 'unittest-json-v1', 'file': REPORT}
        cases = [
            ('python ' + RUNNER, None, 'unregistered-executable'),
            ('python3 ' + RUNNER + ' --pattern $HOME', None, 'unsupported-shell-expansion'),
            ('python3 ' + RUNNER + ' --pattern a.py | cat', None, 'unsupported-shell-form'),
            ('python3 ' + RUNNER + ' --pattern {pattern}', None, 'unsupported-placeholder'),
            ('python3 ' + RUNNER + ' --elenchus-report {report}', None, 'unbound-report-substitution'),
            ('python3 ' + RUNNER + ' --pattern x', contract, 'report-contract'),
            ('python3 ' + RUNNER + ' --elenchus-report {report}',
             {'format': 'unittest-json-v1', 'file': '../escape.json'}, 'report-escape'),
            ('python3 ' + RUNNER + ' --elenchus-report {report}',
             {'format': 'junit-xml', 'file': REPORT}, 'report-contract'),
            ("for file in a b; do python3 " + RUNNER + " --pattern '$file'; done", None,
             'loop-variable-quote-context'),
            ('python3 tests/other.py', None, 'unregistered-cli'),
        ]
        for command, report, reason in cases:
            with self.subTest(command=command):
                self.assertEqual(self.refusal(lambda: gates.validate_command(
                    self.root, command, report, registrations)), reason)

    def test_unbound_arguments_wait_for_the_binding(self):
        data = book().replace(b'--pattern test_core.py', b'--no-such-flag')
        self.assertEqual(results(gates.validate(self.root, data)),
                         ['interface-deferred', 'interface-deferred'])
        digest = self.write_runner()
        reason = self.refusal(lambda: gates.validate(
            self.root, data, require_absent=False, regions_before_implementation=1,
            bindings={RUNNER: digest}, regions_before_binding=1))
        self.assertTrue(reason.startswith('cli-arguments: '), reason)


class BindingTests(Target):
    def bound(self, digest, data=None, **overrides):
        phase = {'require_absent': False, 'regions_before_implementation': 1,
                 'bindings': {RUNNER: digest}, 'regions_before_binding': 1}
        phase.update(overrides)
        return gates.validate(self.root, book() if data is None else data, **phase)

    def test_binding_yields_the_pinned_interface_result(self):
        digest = self.write_runner()
        bound = self.bound(digest)
        self.assertEqual(results(bound), ['interface-valid', 'interface-valid'])
        pinned = gates.validate(self.root, book((RUNNER + ' | build_parser | ' + digest,)))
        self.assertEqual([c['invocations'] for c in bound['commands']],
                         [c['invocations'] for c in pinned['commands']])
        self.assertEqual(bound['commands'][0]['invocations'][0]['cli']['sha256'], digest)

    def test_changed_bound_file_refuses_source_drift(self):
        digest = self.write_runner()
        receipt = self.bound(digest)
        phase = {'regions_before_implementation': 1, 'bindings': {RUNNER: digest},
                 'regions_before_binding': 1}
        gates.replay(self.root, book(), receipt, **phase)
        self.write_runner(RUNNER_PROGRAM + '# audit fix after the push\n')
        self.assertEqual(self.refusal(lambda: self.bound(digest)), 'registered-source-drift')
        self.assertEqual(self.refusal(lambda: gates.replay(self.root, book(), receipt, **phase)),
                         'registered-source-drift')
        (self.root / RUNNER).unlink()
        self.assertEqual(self.refusal(lambda: self.bound(digest)),
                         'source-unavailable: ' + RUNNER)

    def test_bound_file_is_read_without_following_links(self):
        digest = sha(RUNNER_PROGRAM.encode())
        (self.root / 'real.py').write_text(RUNNER_PROGRAM)
        (self.root / 'tests').mkdir()
        (self.root / RUNNER).symlink_to(self.root / 'real.py')
        self.assertEqual(self.refusal(lambda: self.bound(digest)), 'source-unavailable: ' + RUNNER)
        (self.root / RUNNER).unlink()
        (self.root / 'tests').rmdir()
        (self.root / 'tests').symlink_to(self.root)
        self.assertEqual(self.refusal(lambda: self.bound(digest)), 'source-unavailable: ' + RUNNER)

    def test_binding_record_must_match_the_deferred_rows(self):
        digest = self.write_runner()
        other = 'tests/other_runner.py'
        two = book((deferred_row(), deferred_row(other)))
        cases = [
            ({'bindings': {'tests/unknown.py': digest}}, 'deferred-binding-unknown'),
            ({'bindings': {RUNNER: digest, 'tests/unknown.py': digest}}, 'deferred-binding-unknown'),
            ({'data': two}, 'deferred-binding-incomplete'),
            ({'bindings': {RUNNER: digest[:63]}}, 'deferred-binding-invalid'),
            ({'bindings': {RUNNER: digest.upper()}}, 'deferred-binding-invalid'),
            ({'bindings': [(RUNNER, digest)]}, 'deferred-binding-invalid'),
            ({'bindings': {1: digest}}, 'deferred-binding-invalid'),
            ({'regions_before_binding': None}, 'deferred-phase-invalid'),
            ({'bindings': {}}, 'deferred-phase-invalid'),
            ({'regions_before_implementation': None}, 'deferred-phase-invalid'),
            ({'regions_before_implementation': 2, 'regions_before_binding': 1}, 'deferred-phase-invalid'),
            ({'regions_before_binding': 2, 'regions_before_implementation': 2}, 'deferred-phase-invalid'),
            ({'regions_before_implementation': True}, 'deferred-phase-invalid'),
            ({'regions_before_binding': 0}, 'deferred-phase-invalid'),
        ]
        for overrides, reason in cases:
            with self.subTest(overrides=overrides):
                data = overrides.pop('data', None)
                self.assertEqual(self.refusal(lambda: self.bound(digest, data, **overrides)), reason)
        without = book((LOCAL_CLI + ' | main | ' + '0' * 64,))
        self.assertEqual(self.refusal(lambda: self.bound(digest, without)),
                         'deferred-binding-unknown')


class PlacementTests(Target):
    def test_amendment_before_implementation_may_add_a_deferred_row(self):
        data = book((), amendment(deferred_row()))
        self.assertEqual(results(gates.validate(self.root, data)),
                         ['interface-deferred', 'interface-deferred'])
        # Replayed after Step 1 started, the region stays one receipted before it.
        self.write_runner()
        gates.replay(self.root, data, gates.validate(self.root, data, require_absent=False,
                                                     regions_before_implementation=2),
                     regions_before_implementation=2)

    def test_deferred_row_added_after_step_one_starts_refuses(self):
        for data in (book((), amendment(deferred_row())),
                     book((deferred_row(),), amendment(deferred_row(), deferred_row('tests/extra.py'))),
                     book((deferred_row(),), amendment(deferred_row(builder='other_parser'))),
                     book((deferred_row(),), amendment(), amendment(deferred_row(), date='2026-09-28'))):
            with self.subTest(data=data):
                self.assertEqual(self.refusal(lambda: gates.validate(
                    self.root, data, require_absent=False, regions_before_implementation=1)),
                    'deferred-row-after-step-start')

    def test_after_start_amendment_may_repeat_an_unbound_row_byte_for_byte(self):
        (self.root / LOCAL_CLI).parent.mkdir()
        (self.root / LOCAL_CLI).write_text(LOCAL_PROGRAM)
        local = LOCAL_CLI + ' | main | ' + sha(LOCAL_PROGRAM.encode())
        data = book((deferred_row(),), amendment(deferred_row(), local))
        self.write_runner()
        with self.spy() as spy:
            result = gates.validate(self.root, data, require_absent=False,
                                    regions_before_implementation=1)
        self.assert_runner_unread(spy)
        self.assertEqual(results(result), ['interface-deferred', 'interface-deferred'])
        # Retiring the unbound path, or pinning it by digest, adds no deferred row.
        pinned = book((deferred_row(),), amendment(local, RUNNER + ' | build_parser | '
                                                   + sha(RUNNER_PROGRAM.encode())))
        self.assertEqual(results(gates.validate(self.root, pinned, require_absent=False,
                                                regions_before_implementation=1)),
                         ['interface-valid', 'interface-valid'])
        retired = book((deferred_row(),), amendment(local))
        self.assertEqual(gates.capture_runbook(retired, regions_before_implementation=1)[1],
                         {LOCAL_CLI: ('main', sha(LOCAL_PROGRAM.encode()))})
        self.assertEqual(self.refusal(lambda: gates.validate(
            self.root, retired, require_absent=False, regions_before_implementation=1)),
            'unregistered-cli')

    def test_deferred_row_after_binding_refuses_until_a_digest_row_replaces_it(self):
        digest = self.write_runner()
        phase = {'require_absent': False, 'regions_before_implementation': 1,
                 'bindings': {RUNNER: digest}, 'regions_before_binding': 1}
        repeated = book((deferred_row(),), amendment(deferred_row()))
        self.assertEqual(self.refusal(lambda: gates.validate(self.root, repeated, **phase)),
                         'deferred-row-after-binding')
        # A repeat receipted before the binding stays admissible afterwards.
        earlier = dict(phase, regions_before_binding=2)
        self.assertEqual(results(gates.validate(self.root, repeated, **earlier)),
                         ['interface-valid', 'interface-valid'])
        changed = RUNNER_PROGRAM + '# changed in Step 2\n'
        self.write_runner(changed)
        pinned = book((deferred_row(),), amendment(RUNNER + ' | build_parser | ' + sha(changed.encode())))
        self.assertEqual(results(gates.validate(self.root, pinned, **phase)),
                         ['interface-valid', 'interface-valid'])
        retired = book((deferred_row(),), amendment())
        self.assertEqual(self.refusal(lambda: gates.validate(self.root, retired, **phase)),
                         'unregistered-cli')

    def test_phase_boundaries_must_lie_inside_the_document(self):
        for overrides in ({'regions_before_implementation': 2},
                          {'regions_before_implementation': 1, 'bindings': {RUNNER: '0' * 64},
                           'regions_before_binding': 2},
                          {'regions_before_implementation': 0},
                          {'regions_before_implementation': 1.0}):
            with self.subTest(overrides=overrides):
                self.assertEqual(self.refusal(lambda: gates.validate(
                    self.root, book(), require_absent=False, **overrides)), 'deferred-phase-invalid')
        self.assertEqual(gates.capture_runbook(book(), regions_before_implementation=1)[1],
                         {RUNNER: ('build_parser', 'step:1')})

    def test_binding_before_implementation_refuses_inside_the_document(self):
        # S2-R1-01. Both counts lie inside this two-region runbook, so only the
        # ordering rule can refuse. Without it, a deferred row added after the
        # binding would stay unbound.
        digest = self.write_runner()
        late = 'tests/late_runner.py'
        data = book((deferred_row(),),
                    amendment(RUNNER + ' | build_parser | ' + digest, deferred_row(late)))
        phase = {'require_absent': False, 'bindings': {RUNNER: digest}}
        self.assertEqual(self.refusal(lambda: gates.validate(
            self.root, data, regions_before_implementation=2, regions_before_binding=1,
            **phase)), 'deferred-phase-invalid')
        # In order, the late row is a new deferred row after Step 1 started,
        # not a repeat of the bound path.
        self.assertEqual(self.refusal(lambda: gates.validate(
            self.root, data, regions_before_implementation=1, regions_before_binding=1,
            **phase)), 'deferred-row-after-step-start')

    def test_amendment_heading_the_adapter_would_not_count_refuses(self):
        # S2-R2-01. Protasis and Fiat read any whitespace between ``###`` and
        # ``Amendment`` as a dated amendment. Left uncounted, that amendment
        # joins the region before it, so a deferred row it adds after Step 1
        # started would sit in a region receipted before the start.
        plain = ('\n### Amendment -- 2026-09-27\n\n**What changed.** Complete replacement '
                 'Tests: The runner discovers the suite.\n\n**Why.** Fixture.\n\n'
                 '**Steps touched.** Step 1.\n\n**Still holding.** Step 1: entry holds; exit holds.\n')
        late = amendment(deferred_row(), deferred_row('tests/late_runner.py'), date='2026-09-28')
        strict = book((deferred_row(),), plain, late)
        phase = {'require_absent': False, 'regions_before_implementation': 2}
        self.assertEqual(self.refusal(lambda: gates.validate(self.root, strict, **phase)),
                         'deferred-row-after-step-start')
        heading = b'### Amendment -- 2026-09-28'
        for spacing in (b'###  Amendment -- 2026-09-28', b'###\tAmendment -- 2026-09-28'):
            with self.subTest(spacing=spacing):
                loose = strict.replace(heading, spacing)
                self.assertEqual(self.refusal(lambda: gates.validate(self.root, loose, **phase)),
                                 'invalid-registration-amendment')
        # With no deferred row the spacing keeps its earlier reading.
        pinned = LOCAL_CLI + ' | main | ' + sha(LOCAL_PROGRAM.encode())
        legacy = book((pinned,), plain, amendment(pinned, date='2026-09-28')).replace(
            heading, b'###  Amendment -- 2026-09-28')
        self.assertEqual(gates.capture_runbook(legacy)[1],
                         {LOCAL_CLI: ('main', sha(LOCAL_PROGRAM.encode()))})


class ReplayTests(Target):
    def test_unbound_capture_replays_while_the_runner_exists_and_changes(self):
        receipt = gates.validate(self.root, book())
        for text in (RUNNER_PROGRAM, RUNNER_PROGRAM + '# in-step audit fix\n', 'not python\n'):
            with self.subTest(text=text):
                self.write_runner(text)
                with self.spy() as spy:
                    gates.replay(self.root, book(), receipt)
                self.assert_runner_unread(spy)
        forged = copy.deepcopy(receipt)
        forged['commands'][0]['invocations'][0]['result'] = 'interface-valid'
        self.assertEqual(self.refusal(lambda: gates.replay(self.root, book(), forged)),
                         'gate-receipt-drift')

    def test_bound_capture_replays_only_with_its_recorded_binding(self):
        digest = self.write_runner()
        phase = {'regions_before_implementation': 1, 'bindings': {RUNNER: digest},
                 'regions_before_binding': 1}
        receipt = gates.validate(self.root, book(), require_absent=False, **phase)
        before = copy.deepcopy(receipt)
        gates.replay(self.root, book(), receipt, **phase)
        self.assertEqual(receipt, before)
        self.assertEqual(self.refusal(lambda: gates.replay(self.root, book(), receipt)),
                         'gate-receipt-drift')
        unbound = gates.validate(self.root, book(), require_absent=False)
        self.assertEqual(self.refusal(lambda: gates.replay(self.root, book(), unbound, **phase)),
                         'gate-receipt-drift')

    def test_allowlist_admits_exactly_the_reviewed_digests(self):
        self.assertEqual(gates.REPLAY_COMPATIBLE_ADAPTERS, ADMITTED)
        self.assertNotIn(UNADMITTED, gates.REPLAY_COMPATIBLE_ADAPTERS)


class ReleasedAdapterTests(unittest.TestCase):
    """Receipts the admitted released adapters captured, replayed by the successor."""

    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix='deferred-released-')
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name).resolve()
        self.root = self.scratch / 'target'
        for path in gates.REGISTRY:
            destination = self.root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, destination)
        (self.root / LOCAL_CLI).parent.mkdir(parents=True, exist_ok=True)
        (self.root / LOCAL_CLI).write_text(LOCAL_PROGRAM)
        self.data = self.runbook()

    def runbook(self):
        """No deferred row and no Ephoros command: every admitted adapter captures it."""
        exits = ['python3 scripts/run_checks.py --base main --scope root --format json',
                 'for file in README.md AGENTS.md; do python3 '
                 'plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file"; done',
                 'python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py runbook.md --gate-root .',
                 'python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py README.md',
                 'python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests',
                 'python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md',
                 'python3 ' + LOCAL_CLI + ' --root . --count 2']
        text = (fence(LOCAL_CLI + ' | main | ' + sha(LOCAL_PROGRAM.encode())) + '\n'
                '## Step 1: Gate\n\n**Exit.** ' + ' and '.join('`' + c + '`' for c in exits) + '\n\n'
                '**Tests.** Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 '
                '--elenchus-report {report}`; format: `unittest-json-v1`; report file: `' + REPORT + '`.\n\n'
                '## Step 2: Later\n\n**Exit.** `python3 ' + LOCAL_CLI + ' --root .`\n'
                '\n### Amendment -- 2026-09-27\n\n**What changed.** Complete replacement Exit: '
                '`python3 ' + LOCAL_CLI + ' --root . --count 1`\n\n**Why.** Fixture.\n\n'
                '**Steps touched.** Step 2.\n\n**Still holding.** Step 2: entry holds; exit holds.\n')
        return text.encode()

    def test_receipts_from_each_admitted_released_adapter_replay_under_the_successor(self):
        for commit, expected in RELEASED:
            with self.subTest(adapter=expected):
                released = released_adapter(commit, expected, self.scratch)
                receipt = released.validate(self.root, self.data)
                self.assertEqual(receipt['adapter_sha256'], expected)
                self.assertIn('superseded-source', [c.get('result') for c in receipt['commands']])
                before = copy.deepcopy(receipt)
                gates.replay(self.root, self.data, receipt)
                self.assertEqual(receipt, before)
                forged = copy.deepcopy(receipt)
                forged['commands'][0]['command'] += ' --changed'
                with self.assertRaisesRegex(gates.Refusal, '^gate-receipt-drift$'):
                    gates.replay(self.root, self.data, forged)
                for name in (LOCAL_CLI, 'plugins/brevitas/skills/brevitas/scripts/brevitas.py'):
                    original = (self.root / name).read_bytes()
                    (self.root / name).write_bytes(original + b'# reviewed elsewhere\n')
                    try:
                        with self.assertRaises(gates.Refusal):
                            gates.replay(self.root, self.data, receipt)
                    finally:
                        (self.root / name).write_bytes(original)

    def test_unadmitted_adapter_digest_refuses(self):
        receipt = gates.validate(self.root, self.data)
        for adapter in (UNADMITTED, '0' * 64, None):
            with self.subTest(adapter=adapter):
                forged = dict(receipt, adapter_sha256=adapter)
                with self.assertRaisesRegex(gates.Refusal, '^gate-receipt-drift$'):
                    gates.replay(self.root, self.data, forged)

    def test_results_without_deferred_rows_equal_the_released_adapter(self):
        commit, expected = RELEASED[0]
        released = released_adapter(commit, expected, self.scratch)
        subjects = [(self.root, self.data)]
        subjects += [(ROOT, (ROOT / name).read_bytes()) for name in
                     ('docs/protasis-success-criteria/runbook.md',
                      'docs/deferred-runner-binding/runbook.md')]
        for root, data in subjects:
            with self.subTest(root=str(root), runbook=sha(data)):
                fresh = gates.validate(root, data)
                self.assertEqual(fresh, {**released.validate(root, data),
                                         'adapter_sha256': fresh['adapter_sha256']})
        unregistered = (b'## Step 1: Gate\n\n**Exit.** `python3 tests/run_tests.py`\n')
        missing = fence('tests/run_tests.py | build_parser | ' + '0' * 64).encode() + unregistered
        drifted = fence(LOCAL_CLI + ' | main | ' + '0' * 64).encode() + unregistered
        for data in (unregistered, missing, drifted):
            with self.subTest(refusal=data):
                outcomes = []
                for adapter in (released, gates):
                    try:
                        adapter.validate(self.root, data)
                    except adapter.Refusal as exc:
                        outcomes.append(str(exc))
                self.assertEqual(len(outcomes), 2)
                self.assertEqual(outcomes[0], outcomes[1])

    def test_criteria_admission_forwards_the_phase_record(self):
        phase = {'require_absent': False, 'regions_before_implementation': 1,
                 'bindings': {RUNNER: '0' * 64}, 'regions_before_binding': 1}
        declaration = mock.Mock()
        declaration.parse.return_value = {'criteria': []}
        with mock.patch.object(gates, '_success_criteria_module', return_value=declaration), \
                mock.patch.object(gates, 'validate', side_effect=gates.Refusal('forwarded')) as spy:
            with self.assertRaisesRegex(gates.Refusal, '^forwarded$'):
                gates.validate_with_criteria(ROOT, b'declaration', self.data, **phase)
        self.assertEqual(spy.call_args.args, (ROOT, self.data))
        self.assertEqual(spy.call_args.kwargs, phase)


if __name__ == '__main__':
    unittest.main()
