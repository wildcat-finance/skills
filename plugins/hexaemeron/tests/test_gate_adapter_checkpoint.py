"""Archive a signed run captured by a released gate adapter without amendment."""
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

try:
    from . import test_hexctl_checkpoint_archive as archives
    from .test_gate_command_registration import CLI, PROGRAM, RELEASED_ADAPTERS, gates
except ImportError:
    import test_hexctl_checkpoint_archive as archives
    from test_gate_command_registration import CLI, PROGRAM, RELEASED_ADAPTERS, gates


class ReleasedAdapterCheckpointTests(archives.SignedRunFixture):
    def to_receipted_steps(self, titles=('First', 'Second')):
        self.run_ctl('init', '--topic', 'Released gate adapter checkpoint')
        self.write_design_evidence()
        self.write(CLI, PROGRAM)
        study = self.write('study.md', '# Study\n\n```risk-register\nsource | drift | replay\n```\n')
        self.run_ctl('done', 'study', '--artifact', study, '--skills', 'hexaemeron:protasis')
        state = self.state()
        text = (self.design_lock_block(state) + '\n# Runbook\n\n'
                '```command-interfaces\nschema | protasis-command-interfaces/v1\n' +
                CLI + ' | main | ' + gates.digest(PROGRAM.encode()) + '\n```\n\n')
        for number, title in enumerate(titles, 1):
            text += (f'## Step {number}: {title}\n\n**Goal.** Validate.\n'
                     '**Entry.** Source.\n**Exit.** `python3 ' + CLI + ' --root .`\n'
                     '**Files.** ' + CLI + '\n**Tests.** Interface tests.\n'
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
        with patch.dict(os.environ, self.direct_environment(), clear=True), patch.object(module, 'capture_gate_commands', released_capture):
            module.done_runbook(args, state)
        state = self.state()
        step_sources = getattr(self, 'sources_only_on_step_branch', False)
        if step_sources:
            branch = self.step_branch(1, state)
            self.git('branch', branch)
            self.git('checkout', '-q', branch)
        self.git('add', CLI, study, runbook, steps)
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
