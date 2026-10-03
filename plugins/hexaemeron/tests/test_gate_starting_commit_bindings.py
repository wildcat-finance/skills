"""Starting-commit bindings a caller derives: admission, refusal, replay, proof.

The adapter reads no Git for these bindings; its caller derives them. Each
specimen builds its own registered-module source in a scratch root. The one
comparison against the run's starting ref reads that commit's adapter blob
from this repository's history and checks its digest before loading it.
"""
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = 'plugins/hexaemeron/skills/protasis/scripts/gate_commands.py'
PROOF = 'plugins/hexaemeron/tests/fiat_starting_commit_bindings_proof.py'
BREVITAS = 'plugins/brevitas/skills/brevitas/scripts/brevitas.py'
RUN_CHECKS = 'scripts/run_checks.py'
COMMAND = 'python3 ' + BREVITAS + ' one.md'
RUNBOOK = ('**Exit.** `' + COMMAND + '`\n').encode()
# The run's starting commit and the adapter it shipped, which Step 1 left as is.
STARTING_COMMIT = 'dd2e6939ed460dcd987457a398a2765822349588'
STARTING_ADAPTER_SHA256 = '90ad7967e44a583fa5be15f15b804cccdfbd74750e1da19adaae00959dc055f7'
# A digest no release ever carried, standing in for a starting commit's adapter.
BASE_ADAPTER = 'ab' * 32
REVIEWED = frozenset({
    '18eb52e7e6bc741bd2c80c55838de74831777ea0833147570963c10e0904c093',
    'c2d14b0f262ecde17f679a73a462cd2ed0f4305a54528e93e375f2b36514bbc6',
    '00d4c9f2a0905ea65d56a3ddca9a429c9a20d464d9b66f69098a954b5e7c37b0',
    'd7e49768547fe0c4673c8204d3392c57e60824448fac5bfe8a5bdf4ab5c1bef4',
    '3549ce4afff9cdbd3f8ba04beece3eb17d5cb4f51d954f71dd1d50733c237b0c',
    '14a857dc44ce43d7a3771a2125b92f86435e39ab8ba2b027ef02b4f36ca48bad',
    '6f50cd844a3543aa7ef05fc6631c72ba2fd91aab44ad3f06d62bb4f7312682de',
    '550ac4def7d019213a345d1ddf348d3ff263118dc90a425ec091c4fcd47007cf',
})
# A registered interface as its starting commit shipped it. Its module-level
# AST differs from the current pin, so today's adapter refuses it.
MODULE_PROGRAM = '''"""A registered interface, unchanged since its run's starting commit."""
import argparse

REVISION = "starting-commit"


def build_parser():
    parser = argparse.ArgumentParser(description="Fixture registered interface.")
    parser.add_argument("draft", nargs="+")
    parser.add_argument("--format", choices=["human", "json"], default="human")
    return parser
'''
LOCAL_CLI = 'scripts/verify.py'
LOCAL_PROGRAM = '''import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=1)
    args = parser.parse_args()
    return args
'''
RUNNER = 'tests/run_tests.py'
REFUSAL = '^unregistered-cli-module-bindings$'
DRIFT = '^gate-receipt-drift$'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gates = load(ROOT / ADAPTER, 'starting_bindings_gate')
proof = load(ROOT / PROOF, 'starting_bindings_proof')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ast_pin(source, builder='build_parser'):
    """The module digest exactly as ``parser_bindings`` computes it."""
    tree = ast.parse(source)
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == builder]
    functions[0].body = []
    return sha(ast.dump(tree, include_attributes=False).encode())


def fence(*rows):
    return ('```command-interfaces\nschema | protasis-command-interfaces/v1\n'
            + ''.join(row + '\n' for row in rows) + '```\n')


def results(result):
    return [invocation['result'] for command in result['commands']
            for invocation in command.get('invocations', [])]


def without_adapter(result):
    """One result with every adapter digest removed, for cross-adapter equality."""
    stripped = copy.deepcopy(result)
    for holder in (stripped, stripped.get('gate_commands'), stripped.get('join')):
        if isinstance(holder, dict):
            holder.pop('adapter_sha256', None)
    return stripped


def near_miss(digest, index=-1):
    """``digest`` with one hexadecimal character changed: still 64 lowercase hex."""
    position = index % len(digest)
    replacement = '0' if digest[position] != '0' else '1'
    return digest[:position] + replacement + digest[position + 1:]


class Table(dict):
    """A dict subclass sits outside the closed shape."""


class Digest(str):
    """A str subclass sits outside the closed shape."""


def starting_ref_adapter(directory):
    """The adapter at the run's starting commit, loaded only after its digest matches."""
    blob = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
        ['git', '-C', str(ROOT), 'cat-file', 'blob', STARTING_COMMIT + ':' + ADAPTER],
        stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=60).stdout
    if sha(blob) != STARTING_ADAPTER_SHA256:
        raise AssertionError('starting-ref adapter is not ' + STARTING_ADAPTER_SHA256)
    path = Path(directory) / 'starting-ref' / 'gate_commands.py'
    path.parent.mkdir(parents=True)
    path.write_bytes(blob)
    # The criteria join loads its sibling parser, which this step leaves as is.
    sibling = 'success_criteria.py'
    (path.parent / sibling).write_bytes((ROOT / ADAPTER).with_name(sibling).read_bytes())
    return load(path, 'starting_bindings_gate_at_starting_ref')


class Scratch(unittest.TestCase):
    """A disposable root holding one registered module the current pin refuses."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='starting-bindings-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.module = self.root / BREVITAS
        self.module.parent.mkdir(parents=True)
        self.module.write_text(MODULE_PROGRAM)

    def pair(self, source=None):
        data = self.module.read_bytes() if source is None else source
        return {'ast_sha256': ast_pin(data), 'source_sha256': sha(data)}

    def bindings(self, adapter=BASE_ADAPTER, modules=None):
        if modules is None:
            modules = {BREVITAS: self.pair()}
        return {'adapter_sha256': adapter, 'modules': modules}


class ModuleAdmissionTests(Scratch):
    def test_skewed_module_refuses_without_bindings_as_today(self):
        self.assertNotEqual(ast_pin(self.module.read_bytes()), gates.MODULE_BINDINGS[BREVITAS])
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.validate(self.root, RUNBOOK)
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.validate(self.root, RUNBOOK, starting_bindings=None)

    def test_unchanged_module_is_admitted_under_its_starting_pair(self):
        result = gates.validate(self.root, RUNBOOK, starting_bindings=self.bindings())
        self.assertEqual(results(result), ['interface-valid'])
        self.assertEqual(result['commands'][0]['invocations'][0]['cli'],
                         {'path': BREVITAS, 'sha256': sha(self.module.read_bytes()),
                          'declarations_sha256': mock.ANY})
        self.assertEqual(set(result), {'schema', 'artifact_sha256', 'source_root',
                                       'adapter_sha256', 'commands', 'operation_ran'})
        # The result names the adapter that ran, never the supplied digest.
        self.assertEqual(result['adapter_sha256'], sha((ROOT / ADAPTER).read_bytes()))
        self.assertFalse(result['operation_ran'])

    def test_edited_module_refuses_with_todays_cause(self):
        bindings = self.bindings()
        self.module.write_text(MODULE_PROGRAM + '\nEDITED_IN_RUN = 1\n')
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.validate(self.root, RUNBOOK, starting_bindings=bindings)

    def test_source_digest_mismatch_refuses(self):
        bindings = self.bindings()
        # A trailing comment leaves the AST digest alone and moves the source digest.
        self.module.write_text(MODULE_PROGRAM + '# a comment the starting commit lacks\n')
        self.assertEqual(ast_pin(self.module.read_bytes()), bindings['modules'][BREVITAS]['ast_sha256'])
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.validate(self.root, RUNBOOK, starting_bindings=bindings)

    def test_ast_digest_mismatch_refuses(self):
        pinned = self.pair()['ast_sha256']
        for wrong in ('0' * 64, gates.MODULE_BINDINGS[BREVITAS], near_miss(pinned), near_miss(pinned, 0)):
            with self.subTest(ast_sha256=wrong):
                pair = {**self.pair(), 'ast_sha256': wrong}
                with self.assertRaisesRegex(gates.Refusal, REFUSAL):
                    gates.validate(self.root, RUNBOOK,
                                   starting_bindings=self.bindings(modules={BREVITAS: pair}))

    def test_near_miss_source_digest_refuses(self):
        pair = self.pair()
        for index in (-1, 0):
            with self.subTest(index=index):
                wrong = self.bindings(modules={BREVITAS: {**pair, 'source_sha256': near_miss(pair['source_sha256'], index)}})
                # The shape admits the pair; only the digest comparison refuses it.
                self.assertIs(gates.starting_bindings_admitted(wrong), wrong)
                with self.assertRaisesRegex(gates.Refusal, REFUSAL):
                    gates.validate(self.root, RUNBOOK, starting_bindings=wrong)

    def test_malformed_bindings_admit_nothing(self):
        good = self.bindings()
        pair = good['modules'][BREVITAS]
        malformed = [
            [], 'bindings', 42, {}, {'adapter_sha256': BASE_ADAPTER},
            {'modules': good['modules']},
            {**good, 'extra': 1},
            {**good, 'adapter_sha256': None},
            {**good, 'adapter_sha256': BASE_ADAPTER.upper()},
            {**good, 'adapter_sha256': BASE_ADAPTER[:63]},
            {**good, 'adapter_sha256': BASE_ADAPTER + 'a'},
            {**good, 'modules': [pair]},
            {**good, 'modules': {BREVITAS: [pair['ast_sha256'], pair['source_sha256']]}},
            {**good, 'modules': {BREVITAS: {'ast_sha256': pair['ast_sha256']}}},
            {**good, 'modules': {BREVITAS: {**pair, 'blob': 'x'}}},
            {**good, 'modules': {BREVITAS: {**pair, 'source_sha256': 'g' * 64}}},
            {**good, 'modules': {BREVITAS: {**pair, 'ast_sha256': pair['ast_sha256'].upper()}}},
            {**good, 'modules': {'plugins/other.py': pair, BREVITAS: pair}},
            {**good, 'modules': {'': pair, BREVITAS: pair}},
            Table(good),
            {**good, 'adapter_sha256': Digest(BASE_ADAPTER)},
            {**good, 'modules': Table(good['modules'])},
            {**good, 'modules': {BREVITAS: Table(pair)}},
            {**good, 'modules': {BREVITAS: {**pair, 'ast_sha256': Digest(pair['ast_sha256'])}}},
            {**good, 'modules': {BREVITAS: {**pair, 'source_sha256': Digest(pair['source_sha256'])}}},
        ]
        for value in malformed:
            with self.subTest(value=value):
                self.assertIsNone(gates.starting_bindings_admitted(value))
                with self.assertRaisesRegex(gates.Refusal, REFUSAL):
                    gates.validate(self.root, RUNBOOK, starting_bindings=value)
        self.assertIs(gates.starting_bindings_admitted(good), good)

    def test_oversized_bindings_admit_nothing(self):
        pair = self.pair()
        full = {path: pair for path in gates.MODULE_BINDINGS}
        self.assertEqual(len(full), len(gates.MODULE_BINDINGS))
        admitted = gates.validate(self.root, RUNBOOK, starting_bindings=self.bindings(modules=full))
        self.assertEqual(results(admitted), ['interface-valid'])
        oversized = {**full, 'plugins/ninth/module.py': pair}
        self.assertIsNone(gates.starting_bindings_admitted(self.bindings(modules=oversized)))
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.validate(self.root, RUNBOOK, starting_bindings=self.bindings(modules=oversized))
        flood = {**full, **{'flood/%d.py' % index: pair for index in range(4096)}}
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.validate(self.root, RUNBOOK, starting_bindings=self.bindings(modules=flood))

    def test_bindings_for_another_module_do_not_widen_this_one(self):
        elsewhere = self.bindings(modules={RUN_CHECKS: self.pair()})
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.validate(self.root, RUNBOOK, starting_bindings=elsewhere)
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.validate(self.root, RUNBOOK, starting_bindings=self.bindings(modules={}))

    def test_module_matching_the_current_pin_ignores_the_pair(self):
        self.module.write_bytes((ROOT / BREVITAS).read_bytes())
        wrong = {'ast_sha256': '0' * 64, 'source_sha256': '1' * 64}
        result = gates.validate(self.root, RUNBOOK, starting_bindings=self.bindings(modules={BREVITAS: wrong}))
        self.assertEqual(results(result), ['interface-valid'])
        self.assertEqual(without_adapter(result), without_adapter(gates.validate(self.root, RUNBOOK)))

    def test_keyword_threads_through_every_call_path(self):
        bindings = self.bindings()
        tree = ast.parse(self.module.read_bytes(), filename=BREVITAS)
        source_sha = sha(self.module.read_bytes())
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.parser_bindings(tree, 'build_parser', BREVITAS, source_sha)
        gates.parser_bindings(tree, 'build_parser', BREVITAS, source_sha, starting_bindings=bindings)
        # A caller that omits the source digest earns no admission from the pair.
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.parser_bindings(tree, 'build_parser', BREVITAS, starting_bindings=bindings)
        calls = {
            'interface': lambda: gates.interface(self.root, BREVITAS, starting_bindings=bindings),
            'validate_command': lambda: gates.validate_command(self.root, COMMAND,
                                                               starting_bindings=bindings),
            'validate': lambda: gates.validate(self.root, RUNBOOK, starting_bindings=bindings),
            'replay': lambda: gates.replay(
                self.root, RUNBOOK, gates.validate(self.root, RUNBOOK, starting_bindings=bindings),
                starting_bindings=bindings),
        }
        for name, call in calls.items():
            with self.subTest(path=name), \
                    mock.patch.object(gates, 'parser_bindings', wraps=gates.parser_bindings) as spy:
                call()
                self.assertEqual(spy.call_args.kwargs, {'starting_bindings': bindings})
                self.assertEqual(spy.call_args.args[2:], (BREVITAS, source_sha))
        parser, binding = gates.interface(self.root, BREVITAS, starting_bindings=bindings)
        self.assertEqual(binding['path'], BREVITAS)
        self.assertEqual(parser.parse_args(['one.md', '--format', 'json']).format, 'json')
        record = gates.validate_command(self.root, COMMAND, starting_bindings=bindings)
        self.assertEqual([invocation['result'] for invocation in record['invocations']],
                         ['interface-valid'])

    def test_criteria_admission_forwards_the_bindings_to_validate(self):
        bindings = self.bindings()
        declaration = (ROOT / 'docs/protasis-success-criteria/study.md').read_bytes()
        runbook = (ROOT / 'docs/protasis-success-criteria/runbook.md').read_bytes()
        with mock.patch.object(gates, 'validate', wraps=gates.validate) as spy:
            result = gates.validate_with_criteria(ROOT, declaration, runbook,
                                                  starting_bindings=bindings)
        self.assertEqual(spy.call_args.kwargs['starting_bindings'], bindings)
        self.assertEqual(result['schema'], 'protasis-success-criteria-admission/v1')
        self.assertEqual(without_adapter(result),
                         without_adapter(gates.validate_with_criteria(ROOT, declaration, runbook)))
        with mock.patch.object(gates, 'validate', side_effect=gates.Refusal('forwarded')) as spy:
            with self.assertRaisesRegex(gates.Refusal, '^forwarded$'):
                gates.validate_with_criteria(ROOT, declaration, runbook,
                                             starting_bindings=bindings)
        self.assertEqual(spy.call_args.kwargs, {
            'require_absent': True, 'regions_before_implementation': None,
            'bindings': None, 'regions_before_binding': None, 'starting_bindings': bindings})


class ReplayTests(Scratch):
    def receipt(self, adapter, **keywords):
        receipt = gates.validate(ROOT, RUNBOOK, **keywords)
        receipt['adapter_sha256'] = adapter
        return receipt

    def test_replay_substitutes_only_a_matching_starting_adapter_digest(self):
        bindings = {'adapter_sha256': BASE_ADAPTER, 'modules': {}}
        receipt = self.receipt(BASE_ADAPTER)
        before = copy.deepcopy(receipt)
        gates.replay(ROOT, RUNBOOK, receipt, starting_bindings=bindings)
        self.assertEqual(receipt, before)
        for other in ('cd' * 32, '0' * 64, STARTING_ADAPTER_SHA256,
                      near_miss(BASE_ADAPTER), near_miss(BASE_ADAPTER, 0)):
            with self.subTest(differing=other), self.assertRaisesRegex(gates.Refusal, DRIFT):
                gates.replay(ROOT, RUNBOOK, self.receipt(other), starting_bindings=bindings)

    def test_replay_without_bindings_keeps_todays_refusal(self):
        for absent in ({}, {'starting_bindings': None},
                       {'starting_bindings': {'adapter_sha256': BASE_ADAPTER}}):
            with self.subTest(keywords=absent), self.assertRaisesRegex(gates.Refusal, DRIFT):
                gates.replay(ROOT, RUNBOOK, self.receipt(BASE_ADAPTER), **absent)

    def test_replay_still_requires_every_other_field_to_match(self):
        bindings = {'adapter_sha256': BASE_ADAPTER, 'modules': {}}
        # A relocated source_root is the one designed allowance and stays out of this list.
        for field in ('command', 'artifact_sha256', 'operation_ran', 'argv', 'cli', 'schema'):
            with self.subTest(field=field):
                forged = self.receipt(BASE_ADAPTER)
                if field == 'command':
                    forged['commands'][0]['command'] += ' changed.md'
                elif field == 'argv':
                    forged['commands'][0]['invocations'][0]['argv'].append('extra.md')
                elif field == 'cli':
                    forged['commands'][0]['invocations'][0]['cli']['sha256'] = '0' * 64
                elif field == 'schema':
                    forged['schema'] = 'protasis-gate-commands/v2'
                elif field == 'operation_ran':
                    forged['operation_ran'] = True
                else:
                    forged[field] = '0' * 64
                with self.assertRaisesRegex(gates.Refusal, DRIFT):
                    gates.replay(ROOT, RUNBOOK, forged, starting_bindings=bindings)

    def test_reviewed_adapters_still_replay_beside_bindings(self):
        bindings = {'adapter_sha256': BASE_ADAPTER, 'modules': {}}
        for reviewed in sorted(REVIEWED):
            with self.subTest(reviewed=reviewed):
                gates.replay(ROOT, RUNBOOK, self.receipt(reviewed), starting_bindings=bindings)
                gates.replay(ROOT, RUNBOOK, self.receipt(reviewed))

    def test_reviewed_adapter_list_is_unchanged(self):
        self.assertEqual(gates.REPLAY_COMPATIBLE_ADAPTERS, REVIEWED)
        self.assertEqual(gates.RUNNER_SINGLE_PROCESS_ADAPTERS, REVIEWED | {
            'eacd55c44ff05a8a8899143066795bdb1a02fd869c9f4ec12cca55a20252b279',
            '321189fcbcaafdc300d3d2e1663d3d5bf3e704303c04fbf42778cdd2e991357b'})
        self.assertNotIn(BASE_ADAPTER, gates.RUNNER_SINGLE_PROCESS_ADAPTERS)
        self.assertNotIn(STARTING_ADAPTER_SHA256, gates.RUNNER_SINGLE_PROCESS_ADAPTERS)

    def test_replay_admits_a_skewed_module_and_its_starting_adapter_together(self):
        bindings = self.bindings()
        receipt = gates.validate(self.root, RUNBOOK, starting_bindings=bindings)
        receipt['adapter_sha256'] = BASE_ADAPTER
        gates.replay(self.root, RUNBOOK, receipt, starting_bindings=bindings)
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.replay(self.root, RUNBOOK, receipt)
        halves = {**bindings, 'modules': {}}
        with self.assertRaisesRegex(gates.Refusal, REFUSAL):
            gates.replay(self.root, RUNBOOK, receipt, starting_bindings=halves)
        with self.assertRaisesRegex(gates.Refusal, DRIFT):
            gates.replay(self.root, RUNBOOK, receipt,
                         starting_bindings={**bindings, 'adapter_sha256': 'cd' * 32})


class StartingRefParityTests(Scratch):
    def specimens(self):
        """Runbook shapes the existing suites capture, each with the root it needs."""
        report = ('Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py'
                  ' --elenchus-report {report}`; format: `unittest-json-v1`; '
                  'report file: `.hexaemeron/reports/result.json`.')
        loop = ('```sh\nfor file in one.md two.md; do python3 ' + BREVITAS
                + ' "$file"; done\n```\n')
        superseded = ('## Step 1: Check\n\n**Exit.** `' + COMMAND + '`\n\n**Tests.** ' + report
                      + '\n\n### Amendment -- 2026-09-30\n\n**Steps touched.** Step 1.\n\n'
                      '**What changed.** Complete replacement Exit: `' + COMMAND + '`\n')
        local = self.root / LOCAL_CLI
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(LOCAL_PROGRAM)
        local_book = (fence(LOCAL_CLI + ' | main | ' + sha(LOCAL_PROGRAM.encode()))
                      + '\n**Exit.** `python3 ' + LOCAL_CLI + ' --count 2`\n')
        deferred_book = (fence(RUNNER + ' | build_parser | step:1')
                         + '\n## Step 1: Scaffold\n\n**Exit.** `python3 ' + RUNNER
                         + ' --pattern test_core.py`\n')
        return {
            'plain': (ROOT, RUNBOOK),
            'loop': (ROOT, loop.encode()),
            'report': (ROOT, ('**Tests.** ' + report + '\n').encode()),
            'superseded': (ROOT, superseded.encode()),
            'local': (self.root, local_book.encode()),
            'deferred': (self.root, deferred_book.encode()),
        }

    def starting_ref(self):
        adapters = tempfile.TemporaryDirectory(prefix='starting-ref-adapter-')
        self.addCleanup(adapters.cleanup)
        return starting_ref_adapter(adapters.name)

    def test_results_without_the_keyword_equal_the_starting_ref_apart_from_adapter_digest(self):
        released = self.starting_ref()
        self.assertEqual(released.digest((ROOT / ADAPTER).read_bytes()), sha((ROOT / ADAPTER).read_bytes()))
        self.assertNotEqual(sha((ROOT / ADAPTER).read_bytes()), STARTING_ADAPTER_SHA256)
        malformed = {'adapter_sha256': BASE_ADAPTER}
        for name, (root, data) in self.specimens().items():
            with self.subTest(specimen=name):
                expected = released.validate(root, data)
                self.assertEqual(expected['adapter_sha256'], STARTING_ADAPTER_SHA256)
                for keywords in ({}, {'starting_bindings': None}, {'starting_bindings': malformed}):
                    actual = gates.validate(root, data, **keywords)
                    self.assertEqual(without_adapter(actual), without_adapter(expected))
                    self.assertEqual(actual['adapter_sha256'], sha((ROOT / ADAPTER).read_bytes()))
                self.assertEqual(gates.capture_runbook(data), released.capture_runbook(data))
        declaration = (ROOT / 'docs/protasis-success-criteria/study.md').read_bytes()
        runbook = (ROOT / 'docs/protasis-success-criteria/runbook.md').read_bytes()
        self.assertEqual(without_adapter(gates.validate_with_criteria(ROOT, declaration, runbook)),
                         without_adapter(released.validate_with_criteria(ROOT, declaration, runbook)))

    def test_starting_ref_receipt_replays_only_through_the_bindings(self):
        released = self.starting_ref()
        receipt = released.validate(ROOT, RUNBOOK)
        self.assertEqual(receipt['adapter_sha256'], STARTING_ADAPTER_SHA256)
        with self.assertRaisesRegex(gates.Refusal, DRIFT):
            gates.replay(ROOT, RUNBOOK, receipt)
        before = copy.deepcopy(receipt)
        gates.replay(ROOT, RUNBOOK, receipt,
                     starting_bindings={'adapter_sha256': STARTING_ADAPTER_SHA256, 'modules': {}})
        self.assertEqual(receipt, before)
        released.replay(ROOT, RUNBOOK, receipt)

    def test_runbook_with_no_registered_module_gives_the_fixed_result(self):
        released = self.starting_ref()
        _, local_book = self.specimens()['local']
        expected = released.validate(self.root, local_book)
        for bindings in (self.bindings(), self.bindings(modules={}),
                         self.bindings(modules={BREVITAS: {'ast_sha256': '0' * 64,
                                                           'source_sha256': '1' * 64}})):
            with self.subTest(bindings=bindings):
                actual = gates.validate(self.root, local_book, starting_bindings=bindings)
                self.assertEqual(results(actual), ['interface-valid'])
                self.assertEqual(without_adapter(actual), without_adapter(expected))
                self.assertEqual(without_adapter(actual),
                                 without_adapter(gates.validate(self.root, local_book)))

    def test_adapter_reads_no_git_and_imports_nothing_new(self):
        tree = ast.parse((ROOT / ADAPTER).read_bytes(), filename=ADAPTER)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module.split('.')[0])
        self.assertEqual(imported, {'__future__', 'argparse', 'ast', 'copy', 'datetime', 'hashlib',
                                    'importlib', 'os', 'pathlib', 're', 'shlex', 'stat'})
        self.assertNotIn('subprocess', imported)
        self.assertEqual(gates.STARTING_BINDINGS_FIELDS, frozenset({'adapter_sha256', 'modules'}))
        self.assertEqual(gates.STARTING_MODULE_FIELDS, frozenset({'ast_sha256', 'source_sha256'}))


class ProofReporterTests(unittest.TestCase):
    RESOLVER = ('python3 ' + PROOF + ' --candidate base-commit-bindings'
                ' --criterion released-adapter-tests-green'
                ' --report .hexaemeron/reports/design/base-commit-bindings-released-adapter-tests-green.json')

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

    def test_design_record_names_this_reporter_for_the_selected_candidate(self):
        record = json.loads((ROOT / 'docs/starting-commit-gate-bindings/design-evidence.json').read_bytes())
        pending = [row for row in record['results']
                   if row['candidate'] == 'base-commit-bindings' and row['state'] == 'pending']
        resolvers = {row['criterion']: row['resolver'] for row in pending}
        self.assertEqual(resolvers['released-adapter-tests-green'], self.RESOLVER)
        self.assertTrue(resolvers['older-controller-supersession-fixture'].startswith('python3 ' + PROOF + ' '))
        self.assertEqual(proof.NOT_IMPLEMENTED, {})
        self.assertEqual(proof.FIXTURE_CRITERION, 'older-controller-supersession-fixture')
        self.assertEqual(proof.RELEASED_ADAPTER_MODULES, (
            'plugins.hexaemeron.tests.test_gate_commands',
            'plugins.hexaemeron.tests.test_gate_deferred_registration',
            'plugins.hexaemeron.tests.test_gate_starting_commit_bindings'))

    def test_named_refusals_write_nothing(self):
        cases = {
            ('reviewed-prior-pins', 'released-adapter-tests-green'): 'refused: unknown-candidate\n',
            ('base-commit-bindings', 'verify-wall-ms'): 'refused: unknown-criterion\n',
        }
        for (candidate, criterion), message in cases.items():
            with self.subTest(candidate=candidate, criterion=criterion):
                completed = subprocess.run(  # phylax: allow subprocess: fixed argv interpreter, no shell
                    [sys.executable, '-I', '-B', str(ROOT / PROOF), '--candidate', candidate,
                     '--criterion', criterion, '--report', str(self.report)],
                    cwd=self.scratch, capture_output=True, text=True, timeout=120, check=False)
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(completed.stderr, message)
                self.assertEqual(completed.stdout, '')
                self.assertEqual(sorted(os.listdir(self.scratch)), [])

    def test_existing_report_or_link_refuses_before_the_suite_runs(self):
        target = self.scratch / 'keep.json'
        target.write_bytes(b'keep\n')
        link = self.scratch / 'link.json'
        link.symlink_to(target)
        dangling = self.scratch / 'dangling.json'
        dangling.symlink_to(self.scratch / 'absent.json')
        self.report.write_bytes(b'previous\n')
        for path in (self.report, link, dangling):
            with self.subTest(path=path.name), mock.patch.object(proof.subprocess, 'run') as spy:
                code, out, err = self.run_main('--candidate', 'base-commit-bindings',
                                               '--criterion', 'released-adapter-tests-green',
                                               '--report', str(path))
                self.assertEqual((code, out, err), (1, '', 'refused: report-already-exists\n'))
                spy.assert_not_called()
        self.assertEqual(target.read_bytes(), b'keep\n')
        self.assertEqual(self.report.read_bytes(), b'previous\n')
        with mock.patch.object(proof.subprocess, 'run') as spy:
            code, _, err = self.run_main('--candidate', 'base-commit-bindings',
                                         '--criterion', 'released-adapter-tests-green',
                                         '--report', str(self.scratch / '..' / 'escape.json'))
        self.assertEqual((code, err), (1, 'refused: report-path-escape\n'))
        spy.assert_not_called()

    def test_green_suite_writes_one_closed_report_exclusively(self):
        completed = subprocess.CompletedProcess(['python3'], 0, b'', b'')
        with mock.patch.object(proof.subprocess, 'run', return_value=completed) as spy:
            code, out, err = self.run_main('--candidate', 'base-commit-bindings',
                                           '--criterion', 'released-adapter-tests-green',
                                           '--report', str(self.report))
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(out, 'base-commit-bindings/released-adapter-tests-green = True\n')
        self.assertEqual(spy.call_args.args[0],
                         [sys.executable, '-m', 'unittest', *proof.RELEASED_ADAPTER_MODULES])
        self.assertEqual(spy.call_args.kwargs['cwd'], ROOT)
        written = json.loads(self.report.read_bytes())
        self.assertEqual(written, {
            'schema': 'protasis-design-report/v1', 'candidate': 'base-commit-bindings',
            'criterion': 'released-adapter-tests-green', 'value': True, 'unit': 'boolean',
            'command': 'python3 ' + PROOF + ' --candidate base-commit-bindings'
                       ' --criterion released-adapter-tests-green --report ' + str(self.report),
            'exit': 0})
        self.assertEqual(self.report.read_bytes(),
                         (json.dumps(written, indent=2, sort_keys=True) + '\n').encode())
        with mock.patch.object(proof.subprocess, 'run', return_value=completed):
            code, _, err = self.run_main('--candidate', 'base-commit-bindings',
                                         '--criterion', 'released-adapter-tests-green',
                                         '--report', str(self.report))
        self.assertEqual((code, err), (1, 'refused: report-already-exists\n'))
        self.assertEqual(json.loads(self.report.read_bytes()), written)

    def test_report_command_equals_the_recorded_resolver(self):
        completed = subprocess.CompletedProcess(['python3'], 0, b'', b'')
        relative = '.hexaemeron/reports/design/base-commit-bindings-released-adapter-tests-green.json'
        previous = os.getcwd()
        os.chdir(self.scratch)
        self.addCleanup(os.chdir, previous)
        with mock.patch.object(proof.subprocess, 'run', return_value=completed):
            code, _, err = self.run_main('--candidate', 'base-commit-bindings',
                                         '--criterion', 'released-adapter-tests-green',
                                         '--report', relative)
        self.assertEqual((code, err), (0, ''))
        written = json.loads((self.scratch / relative).read_bytes())
        self.assertEqual(written['command'], self.RESOLVER)

    def test_red_suite_writes_nothing(self):
        completed = subprocess.CompletedProcess(['python3'], 1, b'', b'FAILED')
        with mock.patch.object(proof.subprocess, 'run', return_value=completed):
            code, out, err = self.run_main('--candidate', 'base-commit-bindings',
                                           '--criterion', 'released-adapter-tests-green',
                                           '--report', str(self.report))
        self.assertEqual((code, out, err), (1, '', 'refused: released-adapter-tests-red: exit 1\n'))
        self.assertEqual(sorted(os.listdir(self.scratch)), [])


if __name__ == '__main__':
    unittest.main()
