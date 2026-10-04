"""Archive a signed run captured by a released gate adapter without amendment."""
import copy
import contextlib
import importlib.util
import io
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

try:
    from . import test_hexctl_checkpoint_archive as archives
    from . import test_hexctl_checkpoint as capsules
    from .test_gate_command_registration import CLI, PROGRAM, RELEASED_ADAPTERS, gates
except ImportError:
    import test_hexctl_checkpoint_archive as archives
    import test_hexctl_checkpoint as capsules
    from test_gate_command_registration import CLI, PROGRAM, RELEASED_ADAPTERS, gates


class ReleasedAdapterCheckpointTests(archives.SignedRunFixture):
    def to_receipted_steps(self, titles=('First', 'Second')):
        self.run_ctl('init', '--topic', 'Released gate adapter checkpoint')
        self.write_design_evidence()
        self.write(CLI, PROGRAM)
        current_criteria = getattr(self, 'current_criteria', False)
        historical_attempt = getattr(self, 'historical_attempt', False)
        criterion_command = 'python3 ' + CLI + ' --root .'
        measured_cli = 'plugins/brevitas/skills/brevitas/scripts/brevitas.py'
        if historical_attempt:
            distribution = Path(archives.HEXCTL).resolve().parents[5]
            self.write(measured_cli, (distribution / measured_cli).read_text())
            self.write('criterion.md', 'The command succeeds.\n')
            criterion_command = 'python3 ' + measured_cli + ' criterion.md'
        study_text = '# Study\n\n```risk-register\nsource | drift | replay\n```\n'
        if current_criteria:
            study_text += '\n```success-criteria\n' + json.dumps({
                'schema': 'protasis-success-criteria/v1',
                'criteria': [{'id': 'checked', 'claim': 'The command succeeds.',
                              'step': 1 if historical_attempt else 2,
                              'command': criterion_command}],
            }) + '\n```\n'
        study = self.write('study.md', study_text)
        self.run_ctl('done', 'study', '--artifact', study, '--skills', 'hexaemeron:protasis')
        state = self.state()
        text = (self.design_lock_block(state) + '\n# Runbook\n\n'
                '```command-interfaces\nschema | protasis-command-interfaces/v1\n' +
                CLI + ' | main | ' + gates.digest(PROGRAM.encode()) + '\n```\n\n')
        for number, title in enumerate(titles, 1):
            exit_command = criterion_command if historical_attempt and number == 1 else 'python3 ' + CLI + ' --root .'
            tests = ('Elenchus command: `python3 ' + CLI + ' --root . --report {report}`; '
                     'format: `unittest-json-v1`; report file: '
                     f'`.hexaemeron/reports/step-{number}.json`.') if current_criteria else 'Interface tests.'
            text += (f'## Step {number}: {title}\n\n**Goal.** Validate.\n'
                     '**Entry.** Source.\n**Exit.** `' + exit_command + '`\n'
                     '**Files.** ' + CLI + '\n**Tests.** ' + tests + '\n'
                     '**Disciplines.** phylax: parse without imports.\n\n')
        runbook = self.write('runbook.md', text)
        steps = self.write('steps.json', json.dumps(list(titles)))
        module = archives.hexctl_module()
        capture = module.capture_gate_commands

        def released_capture(*args):
            receipt = capture(*args)
            receipt['adapter_sha256'] = RELEASED_ADAPTERS[0]
            return receipt

        args = SimpleNamespace(dir=self.target,
                               artifact=str(Path(self.target, runbook)),
                               steps_file=str(Path(self.target, steps)))
        with patch.dict(os.environ, self.direct_environment(), clear=True):
            if current_criteria:
                module.done_runbook(args, state)
            else:
                with patch.object(module, 'capture_gate_commands', released_capture):
                    module.done_runbook(args, state)
        state = self.state()
        step_sources = getattr(self, 'sources_only_on_step_branch', False)
        if step_sources:
            branch = self.step_branch(1, state)
            self.git('branch', branch)
            self.git('checkout', '-q', branch)
        self.git('add', CLI, study, runbook, steps)
        if historical_attempt:
            self.git('add', measured_cli, 'criterion.md')
        if step_sources:
            self.commit_signed(self.trailers('fixture sources'))
        else:
            self.git('commit', '-q', '-m', 'fixture sources')
        state = self.state()
        self.fake_refs[state['run_branch']] = self.head_sha(state['run_branch'])
        for step in state['steps']:
            branch = self.step_branch(step['n'], state)
            if not (step_sources and step['n'] == 1):
                self.git('branch', branch)
            self.fake_refs[branch] = self.head_sha()
        self.run_ctl('record', 'security_suite', '"waived: fixture"')
        return state

    def implement_step(self, number):
        if not getattr(self, 'historical_attempt', False) or number != 1:
            return super().implement_step(number)
        branch = self.step_branch(number)
        self.git('checkout', '-q', branch)
        head = self.signed_commit(self.trailers(f'step {number}'))
        self.fake_refs[branch] = head
        observed = json.loads(self.run_ctl('run-exit', '--criterion', 'checked').stdout)
        self.assertTrue(observed['settled'], observed)
        module = archives.hexctl_module()
        admission = self.state()['receipts']['runbook']['success_criteria']
        module.criteria_execution_module().validate_result(observed, admission['join'])
        self.run_ctl('done', 'implement', '--branch', branch, '--commit', head)
        return head

    def historical_criteria_archive(self):
        self.current_criteria = True
        self.sources_only_on_step_branch = True
        self.historical_attempt = True
        # This real launcher is the measured executable of an observed child.
        # Removing it after export models an executable absent at recovery.
        tool = Path(self.dir, 'historical-python', 'python3')
        tool.parent.mkdir()
        tool.write_text('#!/bin/sh\nexec ' + repr(archives.sys.executable) + ' "$@"\n')
        tool.chmod(0o700)
        signing_tool = tool.parent / 'verify-signature'
        signing_tool.write_text('#!/bin/sh\nexec ' + repr(self.tool_paths['gpg']) +
                               ' --homedir ' + repr(self.key_home) + ' "$@"\n')
        signing_tool.chmod(0o700)
        self.git('config', 'gpg.program', str(signing_tool))
        self.env['PATH'] = str(tool.parent) + os.pathsep + self.env['PATH']
        self.to_post_push()
        attempt = self.state()['receipts']['runbook']['success_criteria']['attempts'][0]
        self.assertTrue(attempt['settled'])
        self.assertEqual(attempt['invocations'][0]['executable']['path'], str(tool))
        self.run_ctl('verify')
        if getattr(self, 'max_controller_files', False):
            module = archives.hexctl_module()
            root = Path(self.target, '.hexaemeron')
            count = len(module._checkpoint_snapshot(str(root), None))
            for number in range(module.CHECKPOINT_FILES_MAX - count):
                (root / f'limit-{number:04d}').write_bytes(b'x')
            self.assertEqual(len(module._checkpoint_snapshot(str(root), None)),
                             module.CHECKPOINT_FILES_MAX)
        _, exported = self.archive()
        tool.unlink()
        return self.published(), exported, attempt

    def test_criteria_history_retains_a_capsule_at_controller_file_limit(self):
        self.max_controller_files = True
        archive, exported, _ = self.historical_criteria_archive()
        restored = json.loads(archives.CheckpointArchiveRestoreTests.run_restore(
            self, archive, exported['outer_sha256'], Path(self.dir, 'criteria-limit-origin')).stdout)
        self.assertEqual(restored['verify'], 'ok')

    def test_criteria_free_internal_boundary_does_not_load_absent_adapter(self):
        self.to_post_push()
        self.run_ctl('verify')
        state = self.state()
        isolated_runtime = Path(self.dir, 'pre-criteria-runtime')
        isolated_runtime.mkdir()
        controller = isolated_runtime / 'hexctl.py'
        controller.write_bytes(Path(archives.HEXCTL).read_bytes())
        self.assertFalse((isolated_runtime / 'criteria_execution.py').exists())
        spec = importlib.util.spec_from_file_location('pre_criteria_controller', controller)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIsNone(module.success_criteria_admission(state))
        legacy = copy.deepcopy(state)
        legacy['contracts'].pop('success_criteria', None)
        for name, checked_state in (('legacy', legacy), ('optional-criteria', state)):
            with self.subTest(contract=name):
                expected = module._next_directive(checked_state)
                manifest = {'boundary': {'next': expected}}
                # Isolate the internal semantic boundary after the independent
                # verify/status checks, with an actually absent runtime sibling.
                with patch.object(module, 'verify_run', return_value=1), \
                        patch.object(module, 'cmd_status'), \
                        patch.object(module, 'load_state', return_value=checked_state):
                    try:
                        result = module._checkpoint_restore_internal_checks(
                            self.target, manifest, b'')
                    except FileNotFoundError as error:
                        self.fail(f'criteria-free internal NEXT loaded an absent adapter: {error}')
                self.assertEqual(result[1], expected)

    def test_ordinary_criteria_replay_preserves_ledger_reader_compatibility(self):
        _, _, attempt = self.historical_criteria_archive()
        tool = Path(attempt['invocations'][0]['executable']['path'])
        tool.write_text('#!/bin/sh\nexec ' + repr(archives.sys.executable) + ' "$@"\n')
        tool.chmod(0o700)
        self.run_ctl('verify')
        ledger = Path(self.target, '.hexaemeron/ledger.jsonl')
        entries = [json.loads(line) for line in ledger.read_bytes().splitlines()]
        entries[0]['reader_extension'] = True
        ledger.write_bytes(b'\n' + b''.join(
            json.dumps(row, sort_keys=True).encode() + b'\n\n' for row in entries))
        before = self.controller_bytes()
        self.run_ctl('verify')
        self.assertEqual(self.controller_bytes(), before)
        os.link(ledger, Path(self.dir, 'ordinary-ledger-link'))
        self.run_ctl('verify')
        self.assertEqual(self.controller_bytes(), before)

    def extracted_criteria_capsule(self, archive):
        capsule = Path(self.dir, 'original-criteria-capsule')
        capsule.mkdir()
        with zipfile.ZipFile(archive) as container:
            for name in container.namelist():
                prefix = 'controller-capsule/'
                if name.startswith(prefix) and not name.endswith('/'):
                    output = capsule / name.removeprefix(prefix)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(container.read(name))
        return capsule, gates.digest((capsule / 'MANIFEST.json').read_bytes())

    def test_interrupted_criteria_capsule_copy_can_retry_from_the_original(self):
        archive, _, _ = self.historical_criteria_archive()
        capsule, digest = self.extracted_criteria_capsule(archive)
        origin, _ = capsules.HexctlCheckpointTests.fresh_origin_for(self, capsule)
        subprocess.run(['git', '-C', str(origin), 'remote', 'set-url', 'origin',
                        archives.ORIGIN_URL], check=True, capture_output=True)
        module = archives.hexctl_module()
        original_snapshot = module._checkpoint_snapshot

        def interrupted(source, destination, **kwargs):
            if destination is not None and module.CRITERIA_CHECKPOINT_HISTORY_DIR in destination:
                Path(destination, 'interrupted').write_bytes(b'partial')
                raise SystemExit(74)
            return original_snapshot(source, destination, **kwargs)

        arguments = SimpleNamespace(dir=str(origin), source=str(capsule), manifest_sha256=digest)
        with patch.dict(os.environ, self.direct_environment(), clear=True):
            with patch.object(module, '_checkpoint_snapshot', interrupted):
                with self.assertRaises(SystemExit) as stopped:
                    module.cmd_checkpoint_restore(arguments)
        self.assertEqual(stopped.exception.code, 74)
        history = origin / '.git' / module.CRITERIA_CHECKPOINT_HISTORY_DIR
        self.assertFalse((history / digest).exists())
        self.assertTrue((origin / '.hexaemeron/checkpoint-restore.json').is_file())
        restored = capsules.HexctlCheckpointTests.restore_into(self, origin, capsule, digest)
        self.assertEqual(json.loads(restored.stdout)['verify'], 'ok')
        self.assertTrue((history / digest / 'MANIFEST.json').is_file())
        self.assertFalse((origin / '.hexaemeron/checkpoint-restore.json').exists())

    def test_archived_criteria_attempt_replays_without_original_executable(self):
        archive, exported, attempt = self.historical_criteria_archive()
        before = self.controller_bytes()
        destination = Path(self.dir, 'historical-criteria-origin')
        restored = json.loads(archives.CheckpointArchiveRestoreTests.run_restore(
            self, archive, exported['outer_sha256'], destination).stdout)
        worktree = Path(restored['restore']['worktree'])
        state = json.loads((worktree / '.hexaemeron/state.json').read_bytes())
        self.assertEqual(state['receipts']['runbook']['success_criteria']['attempts'], [attempt])
        fresh = subprocess.run([archives.sys.executable, archives.HEXCTL, '--dir', str(worktree),
                                'verify'], env=self.direct_environment(),
                               capture_output=True, text=True)
        self.assertEqual(fresh.returncode, 0, fresh.stderr)
        later = subprocess.run([archives.sys.executable, archives.HEXCTL, '--dir', str(worktree),
                                'record', 'restored_note', '"continued"'],
                               env=self.direct_environment(), capture_output=True, text=True)
        self.assertEqual(later.returncode, 0, later.stderr)
        fresh = subprocess.run([archives.sys.executable, archives.HEXCTL, '--dir', str(worktree),
                                'verify'], env=self.direct_environment(),
                               capture_output=True, text=True)
        self.assertEqual(fresh.returncode, 0, fresh.stderr)
        candidate = worktree / '.hexaemeron/continued-runbook.md'
        candidate.write_bytes((worktree / 'runbook.md').read_bytes() + (
            '\n### Amendment -- 2026-10-04\n\n'
            '**What changed.** Complete replacement Files: `scripts/verify.py` and notes.\n\n'
            '**Why.** Keep the reviewed runbook current.\n\n'
            '**Steps touched.** Step 2.\n\n'
            '**Still holding.** Step 2: entry holds; exit holds.\n').encode())
        amended = subprocess.run([archives.sys.executable, archives.HEXCTL, '--dir', str(worktree),
                                  'amend', 'runbook', '--artifact', str(candidate)],
                                 env=self.direct_environment(), capture_output=True, text=True)
        self.assertEqual(amended.returncode, 0, amended.stderr)
        fresh = subprocess.run([archives.sys.executable, archives.HEXCTL, '--dir', str(worktree),
                                'verify'], env=self.direct_environment(),
                               capture_output=True, text=True)
        self.assertEqual(fresh.returncode, 0, fresh.stderr)
        admission = json.loads((worktree / '.hexaemeron/state.json').read_bytes())[
            'receipts']['runbook']['success_criteria']
        self.assertEqual(admission['attempts'], [attempt])
        self.assertEqual(len(admission['history']['versions']), 2)
        self.assertEqual(self.controller_bytes(), before)

    def test_restored_criteria_custody_refuses_mutation_and_new_attempt_claims(self):
        archive, exported, attempt = self.historical_criteria_archive()
        destination = Path(self.dir, 'guarded-criteria-origin')
        restored = json.loads(archives.CheckpointArchiveRestoreTests.run_restore(
            self, archive, exported['outer_sha256'], destination).stdout)
        worktree = Path(restored['restore']['worktree'])
        state_path = worktree / '.hexaemeron/state.json'
        ledger_path = worktree / '.hexaemeron/ledger.jsonl'
        state_bytes, ledger_bytes = state_path.read_bytes(), ledger_path.read_bytes()
        state = json.loads(state_bytes)
        module = archives.hexctl_module()
        adapter = module.criteria_execution_module()
        admission = state['receipts']['runbook']['success_criteria']
        join = module._criteria_attempt_join(admission, attempt)
        cache = next((destination / '.git' / module.CRITERIA_CHECKPOINT_HISTORY_DIR).glob('[0-9a-f]' * 64))
        manifest_bytes = (cache / 'MANIFEST.json').read_bytes()

        def restore_controller():
            state_path.write_bytes(state_bytes)
            ledger_path.write_bytes(ledger_bytes)

        def refusal(factory, token=None):
            with self.assertRaises((adapter.Refusal, SystemExit)) as stopped:
                factory()
            if token is not None:
                self.assertIn(token, str(stopped.exception))

        with patch.dict(os.environ, self.direct_environment(), clear=True):
            validator = module._criteria_result_validator(str(worktree), state, adapter)
            self.assertIs(validator(attempt, join, run_id=attempt['run_id'],
                                    init_id=attempt['init_id'], step=1,
                                    criterion_id='checked'), attempt)
            module._criteria_all_success(str(worktree), state)
            self.assertIsNotNone(module._criteria_terminal_receipt(str(worktree), state))
            self.assertIsNone(module._criteria_next_directive(
                None, state, state['steps'][0], validator=validator))
            for name, mutate in (
                ('observed-type', lambda row: row.update(observed=1)),
                ('operation-type', lambda row: row.update(operation_ran=1)),
                ('command', lambda row: row.update(command='python3 changed.py')),
                ('group', lambda row: row.update(criterion_ids=['changed'])),
                ('outcome', lambda row: row['outcomes'][0]['stdout'].update(sha256='0' * 64)),
                ('source', lambda row: row['source_before'].update(commit='0' * 40)),
                ('executable', lambda row: row['invocations'][0]['executable'].update(sha256='0' * 64)),
                ('argv', lambda row: row['invocations'][0]['resolved_argv'].__setitem__(1, 'changed.py')),
            ):
                changed = copy.deepcopy(attempt)
                mutate(changed)
                with self.subTest(record=name):
                    refusal(lambda: validator(changed, join), 'checkpoint-criteria-result-drift')
            changed_join = copy.deepcopy(join)
            changed_join['criteria'][0]['claim'] = 'Changed historical declaration.'
            refusal(lambda: validator(attempt, changed_join), 'checkpoint-criteria-result-drift')

            for name, mutate, token in (
                ('attempt-prefix', lambda row: row['receipts']['runbook']['success_criteria']['attempts'][0]['outcomes'][0]['stdout'].update(sha256='0' * 64), 'checkpoint-criteria-attempt-prefix'),
                ('history-prefix', lambda row: row['receipts']['runbook']['success_criteria']['history']['versions'][0].update(study_sha256='0' * 64), 'checkpoint-criteria-history-prefix'),
            ):
                changed = copy.deepcopy(state)
                mutate(changed)
                module.commit(str(worktree), changed, 'record', {'key': 'guard', 'value': name})
                with self.subTest(context=name):
                    refusal(lambda: module._criteria_result_validator(str(worktree), changed, adapter), token)
                restore_controller()

            for duplicate in (True, False):
                changed = copy.deepcopy(state)
                suffix = copy.deepcopy(attempt)
                if not duplicate:
                    suffix['attempt_id'] = 'post-restore-observation'
                changed['receipts']['runbook']['success_criteria']['attempts'].append(suffix)
                module.commit(str(worktree), changed, 'run-exit', {'attempt': suffix})
                if duplicate:
                    refusal(lambda: module._criteria_result_validator(str(worktree), changed, adapter),
                            'checkpoint-criteria-attempts')
                else:
                    checked = module._criteria_result_validator(str(worktree), changed, adapter)
                    refusal(lambda: checked(suffix, join), 'result-executable')
                restore_controller()

            entries = [json.loads(line) for line in ledger_bytes.splitlines()]
            entries[0]['data']['topic'] = 'Changed original source history.'
            previous = 'genesis'
            for entry in entries:
                entry['prev'] = previous
                entry['hash'] = gates.digest(module.canonical({key: entry[key] for key in
                    ('ts', 'event', 'data', 'prev', 'state')}).encode())
                previous = entry['hash']
            ledger_path.write_bytes(b''.join(json.dumps(row, sort_keys=True).encode() + b'\n'
                                            for row in entries))
            refusal(lambda: module._criteria_result_validator(str(worktree), state, adapter),
                    'checkpoint-criteria-restore-binding')
            restore_controller()
            event = next(row for row in entries if row['event'] == 'checkpoint:restore')
            module.commit(str(worktree), state, 'checkpoint:restore', event['data'])
            refusal(lambda: module._criteria_result_validator(str(worktree), state, adapter),
                    'checkpoint-criteria-restore-count')
            restore_controller()

            (cache / 'MANIFEST.json').write_bytes(b'x' + manifest_bytes[1:])
            refusal(lambda: module._criteria_result_validator(str(worktree), state, adapter))
            (cache / 'MANIFEST.json').write_bytes(manifest_bytes)
            link = destination / 'manifest-hardlink'
            os.link(cache / 'MANIFEST.json', link)
            refusal(lambda: module._criteria_result_validator(str(worktree), state, adapter))
            link.unlink()
            moved = cache.with_name('.preserved-for-guard')
            cache.rename(moved)
            refusal(lambda: module._criteria_result_validator(str(worktree), state, adapter))
            cache.symlink_to(moved, target_is_directory=True)
            refusal(lambda: module._criteria_result_validator(str(worktree), state, adapter))
            cache.unlink()
            moved.rename(cache)

            unknown_source = destination / 'unknown-criteria-execution.py'
            unknown_source.write_bytes(Path(adapter.__file__).read_bytes() + b'\n# unknown adapter\n')
            spec = importlib.util.spec_from_file_location('unknown_criteria_execution', unknown_source)
            unknown = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(unknown)
            strict = module._criteria_result_validator(str(worktree), state, unknown)
            with self.assertRaisesRegex(unknown.Refusal, 'result-executable'):
                strict(attempt, join)
            self.assertEqual(state_path.read_bytes(), state_bytes)
            self.assertEqual(ledger_path.read_bytes(), ledger_bytes)
            self.assertEqual((cache / 'MANIFEST.json').read_bytes(), manifest_bytes)

    def test_criteria_cache_occupied_digest_refuses_without_replacement(self):
        archive, _, _ = self.historical_criteria_archive()
        capsule, digest = self.extracted_criteria_capsule(archive)
        origin, _ = capsules.HexctlCheckpointTests.fresh_origin_for(self, capsule)
        subprocess.run(['git', '-C', str(origin), 'remote', 'set-url', 'origin',
                        archives.ORIGIN_URL], check=True, capture_output=True)
        module = archives.hexctl_module()
        occupied = origin / '.git' / module.CRITERIA_CHECKPOINT_HISTORY_DIR / digest
        occupied.mkdir(parents=True)
        preserved = occupied / 'unowned'
        preserved.write_bytes(b'do not replace')
        refused = capsules.HexctlCheckpointTests.restore_into(self, origin, capsule, digest, expect=2)
        self.assertIn('unsupported top-level entry', refused.stderr)
        self.assertEqual(preserved.read_bytes(), b'do not replace')
        self.assertTrue((origin / '.hexaemeron/checkpoint-restore.json').is_file())

        # Exercise the reader's private historical validator at a due step.
        # NEXT handles Refusal from each adapter load through its ValueError base.
        def due_step(state):
            state['current_step'] = 1
            state['steps'][0]['phase'] = 'implement'

        capsules.HexctlCheckpointTests.rewrite_capsule_state(capsule, due_step)
        state_path = capsule / 'controller/state.json'
        ledger_path = capsule / 'controller/ledger.jsonl'
        state = json.loads(state_path.read_bytes())
        adapter = module.criteria_execution_module()
        validator = module._criteria_capsule_validator(state, ledger_path.read_bytes(), adapter)
        directive = module._next_directive(state, criteria_validator=validator)
        self.assertEqual(directive['do'], 'implement')
        manifest_path = capsule / 'MANIFEST.json'
        manifest = json.loads(manifest_path.read_bytes())
        manifest['boundary']['next'] = directive
        manifest_path.write_bytes(module.canonical(manifest).encode() + b'\n')
        digest = gates.digest(manifest_path.read_bytes())
        module._checkpoint_restore_capsule(str(capsule), digest)

        def internal_checks(checked_state, checked_validator):
            # Verification and status have their own guards. This unit seam
            # isolates the real semantic NEXT call and its private callback.
            with patch.object(module, 'verify_run', return_value=1), \
                    patch.object(module, 'cmd_status'), \
                    patch.object(module, 'load_state', return_value=checked_state), \
                    patch.object(module, '_criteria_result_validator', return_value=checked_validator), \
                    patch.object(module, 'criteria_execution_module', side_effect=[adapter, module.criteria_execution_module()]):
                return module._checkpoint_restore_internal_checks(str(origin), manifest, b'')

        self.assertEqual(internal_checks(state, validator)[1], directive)
        state['receipts']['runbook']['success_criteria']['attempts'][0][
            'invocations'][0]['executable']['sha256'] = 'malformed'
        entries = [json.loads(line) for line in ledger_path.read_bytes().splitlines()]
        for entry in entries:
            if entry['event'] == 'run-exit':
                entry['data']['attempt'] = copy.deepcopy(
                    state['receipts']['runbook']['success_criteria']['attempts'][0])
        previous = 'genesis'
        for entry in entries:
            entry['prev'] = previous
            entry['hash'] = gates.digest(module.canonical({key: entry[key] for key in
                ('ts', 'event', 'data', 'prev', 'state')}).encode())
            previous = entry['hash']
        ledger_path.write_bytes(b''.join(json.dumps(row, sort_keys=True).encode() + b'\n'
                                        for row in entries))
        digest = capsules.HexctlCheckpointTests.rewrite_capsule_state(
            capsule, lambda row: row.update(state))
        validator = module._criteria_capsule_validator(state, ledger_path.read_bytes(), adapter)
        for boundary, read, code, reason in (
            ('capsule-reader', lambda: module._checkpoint_restore_capsule(str(capsule), digest),
             2, 'checkpoint boundary does not match controller semantics'),
            ('internal-next', lambda: internal_checks(state, validator),
             1, 'checkpoint restored next directive changed'),
        ):
            with self.subTest(boundary=boundary):
                message = io.StringIO()
                with contextlib.redirect_stderr(message):
                    with self.assertRaises(BaseException) as stopped:
                        read()
                self.assertIsInstance(stopped.exception, SystemExit)
                self.assertEqual(stopped.exception.code, code)
                self.assertIn(reason, message.getvalue())

    def test_released_gate_receipt_survives_signed_archive_inspection_and_restore(self):
        self.to_post_push()
        before = self.controller_bytes()
        receipt = self.state()['receipts']['runbook']['gate_commands']
        self.assertEqual(receipt['adapter_sha256'], RELEASED_ADAPTERS[0])
        self.run_ctl('verify')
        _, result = self.archive()
        self.assertEqual(self.controller_bytes(), before)
        archive = self.published()
        with zipfile.ZipFile(archive) as container:
            self.assertEqual(container.read('controller-capsule/controller/state.json'), before[0])
            self.assertEqual(container.read('controller-capsule/controller/ledger.jsonl'), before[1])
        archives.CheckpointArchiveInspectTests.run_inspect(self, archive, result['outer_sha256'], expect=0)
        restored = archives.CheckpointArchiveRestoreTests.run_restore(
            self, archive, result['outer_sha256'], Path(self.dir, 'restored-origin'))
        payload = json.loads(restored.stdout)
        self.assertEqual(payload['verify'], 'ok')
        worktree = Path(payload['restore']['worktree'])
        state = json.loads((worktree / '.hexaemeron/state.json').read_bytes())
        self.assertEqual(state['receipts']['runbook']['gate_commands'], receipt)
        self.assertEqual(self.controller_bytes(), before)

    def test_fixed_gate_source_absent_from_run_branch_restores_from_step_archive(self):
        """Archive restore preserves fixed gates, refs and identity from the step tree."""
        self.sources_only_on_step_branch = True
        self.to_post_push()
        state = self.state()
        self.assertNotIn('gate_binding', state['steps'][0]['receipts']['push'])
        self.assertEqual(self.git('ls-tree', state['run_branch'], '--', CLI).stdout, '')
        self.assertEqual(Path(self.target, CLI).read_bytes(), PROGRAM.encode())
        before = self.controller_bytes()
        _, exported = self.archive()
        archive = self.published()
        with zipfile.ZipFile(archive) as container:
            manifest = json.loads(container.read('checkpoint.json'))
            self.assertEqual(container.read('controller-capsule/controller/state.json'), before[0])
            self.assertEqual(container.read('controller-capsule/controller/ledger.jsonl'), before[1])
        self.assertEqual(manifest['identity']['status'], 'bound')
        destination = Path(self.dir, 'fixed-gate-restored-origin')
        result = archives.CheckpointArchiveRestoreTests.run_restore(
            self, archive, exported['outer_sha256'], destination)
        restored = json.loads(result.stdout)
        worktree = Path(restored['restore']['worktree'])
        branch = subprocess.run(['git', 'symbolic-ref', '--short', 'HEAD'], cwd=worktree,
                                capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(branch, self.step_branch(1))
        self.assertEqual((worktree / CLI).read_bytes(), PROGRAM.encode())
        self.assertEqual(restored['verify'], 'ok')
        self.assertEqual(restored['next'], manifest['boundary']['next'])
        self.assertEqual(restored['snapshot_id'], manifest['identity']['snapshot_id'])
        self.assertEqual(restored['restore']['refs'], len(manifest['refs']))
        for ref, expected in manifest['refs'].items():
            observed = subprocess.run(['git', '-C', str(destination), 'rev-parse', '--verify',
                                       ref + '^{commit}'], capture_output=True, text=True, check=True)
            self.assertEqual(observed.stdout.strip(), expected)
        self.assertEqual(self.controller_bytes(), before)
        (worktree / CLI).write_text(PROGRAM + '# changed after restore\n', encoding='utf-8')
        refused = subprocess.run([archives.sys.executable, archives.HEXCTL, '--dir', str(worktree),
                                  'verify'], capture_output=True, text=True)
        self.assertEqual(refused.returncode, 1, refused.stderr)
        self.assertIn('registered-source-drift', refused.stderr)

    def test_current_criteria_report_receipt_survives_signed_archive_relocation(self):
        self.current_criteria = True
        self.sources_only_on_step_branch = True
        self.to_post_push()
        before = self.controller_bytes()
        admission = self.state()['receipts']['runbook']['success_criteria']
        gate = admission['gate_commands']
        self.assertEqual(gate['adapter_sha256'], gates.digest(Path(gates.__file__).read_bytes()))
        self.assertEqual(admission.get('attempts', []), [])
        self.assertFalse(admission['operation_ran'])
        report_commands = [row for row in gate['commands'] if row.get('report')]
        self.assertEqual(len(report_commands), 2)
        self.assertEqual(self.git('ls-tree', self.state()['run_branch'], '--', CLI).stdout, '')
        _, exported = self.archive()
        archive = self.published()
        manifest = self.manifest_of(archive)
        restored = json.loads(archives.CheckpointArchiveRestoreTests.run_restore(
            self, archive, exported['outer_sha256'], Path(self.dir, 'current-criteria-origin')).stdout)
        worktree = Path(restored['restore']['worktree'])
        restored_state = json.loads((worktree / '.hexaemeron/state.json').read_bytes())
        self.assertNotEqual(str(worktree), gate['source_root'])
        self.assertEqual(restored_state['receipts']['runbook']['success_criteria'], admission)
        self.assertEqual(restored['verify'], 'ok')
        self.assertEqual(restored['next'], manifest['boundary']['next'])
        self.assertEqual(restored['snapshot_id'], manifest['identity']['snapshot_id'])
        self.assertEqual((worktree / CLI).read_bytes(), PROGRAM.encode())
        for command in report_commands:
            self.assertFalse((worktree / command['report']['file']).exists())
        self.assertEqual(self.controller_bytes(), before)

    def test_criteria_replay_refuses_non_false_operation_claims(self):
        self.current_criteria = True
        self.to_receipted_steps()
        module = archives.hexctl_module()
        state = self.state()
        entries = [json.loads(line) for line in Path(
            self.target, '.hexaemeron/ledger.jsonl').read_text().splitlines()]
        event = next(row['data'] for row in entries if row['event'] == 'done:runbook')
        gate = state['receipts']['runbook']['success_criteria']['gate_commands']
        before = self.controller_bytes()
        with patch.dict(os.environ, self.direct_environment(), clear=True):
            for recovery in (False, True):
                keywords = {'recovery_gate': gate} if recovery else {}
                module.verify_success_criteria(
                    self.target, state, entries[0], event, [], [], **keywords)
                for operation in (0, 1, None, True, 'false', [], {}):
                    forged = copy.deepcopy(state)
                    forged['receipts']['runbook']['success_criteria']['operation_ran'] = operation
                    with self.subTest(recovery=recovery, operation=operation):
                        with self.assertRaises(SystemExit) as refused:
                            module.verify_success_criteria(
                                self.target, forged, entries[0], event, [], [], **keywords)
                        self.assertEqual(refused.exception.code, 1)
        self.assertEqual(self.controller_bytes(), before)

    def test_current_criteria_replay_refuses_missing_or_non_object_gate(self):
        self.current_criteria = True
        self.to_receipted_steps()
        module = archives.hexctl_module()
        state = self.state()
        entries = [json.loads(line) for line in Path(
            self.target, '.hexaemeron/ledger.jsonl').read_text().splitlines()]
        event = next(row['data'] for row in entries if row['event'] == 'done:runbook')
        before = self.controller_bytes()
        with patch.dict(os.environ, self.direct_environment(), clear=True):
            module.verify_success_criteria(self.target, state, entries[0], event, [], [])
            for shape, value in (('missing', None), ('none', None), ('zero', 0),
                                 ('list', []), ('string', 'gate')):
                forged = copy.deepcopy(state)
                admission = forged['receipts']['runbook']['success_criteria']
                if shape == 'missing':
                    del admission['gate_commands']
                else:
                    admission['gate_commands'] = value
                with self.subTest(shape=shape):
                    with self.assertRaises(BaseException) as refused:
                        module.verify_success_criteria(
                            self.target, forged, entries[0], event, [], [])
                    self.assertIsInstance(refused.exception, SystemExit)
                    self.assertEqual(refused.exception.code, 1)
        self.assertEqual(self.controller_bytes(), before)
