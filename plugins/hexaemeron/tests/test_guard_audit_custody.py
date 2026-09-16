"""Keep receipted audit bytes usable after their required Git commit."""
import contextlib
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock


from hexctl_harness import hexctl_module


CANDIDATE = hexctl_module()
LOG = 'audit/rounds/fixture.md'
VIEW = 'audit/rounds/fixture.synopsis.md'
RAW = (
    '## Step 1, round 1 -- 2026-09-16T00:00:00Z\n\n'
    'Audit schema: fiat-audit-round/v2\n\n'
    'Covered: fixture=reviewed\n\n'
    'Not checked: none\n\n'
    'Elenchus verdict: null\n\n'
    '| id | severity | file | finding | status |\n'
    '| --- | --- | --- | --- | --- |\n'
    '| -- | -- | -- | none | -- |\n\n'
    'Leads not pursued: none\n'
).encode()


class NativeGuardAuditPairTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='audit-custody-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Disposable fixture')
        self.git('config', 'user.email', 'fixture@example.test')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('config', 'core.hooksPath', '/dev/null')
        (self.root / 'baseline').write_bytes(b'fixture\n')
        self.git('add', 'baseline')
        self.git('commit', '-qm', 'Unsigned disposable fixture baseline')
        self.state = {'config': {'audit': {'log_path': LOG}}, 'steps': []}

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True,
                              check=True, timeout=20).stdout

    def pair(self, raw=RAW, *, commit=False):
        rendered = CANDIDATE._guard_audit_synopsis_module().render_source(LOG, raw)
        (self.root / LOG).parent.mkdir(parents=True, exist_ok=True)
        (self.root / LOG).write_bytes(raw)
        (self.root / VIEW).write_bytes(rendered['bytes'])
        self.state['steps'] = [{'audit': {'rounds': [{
            'log': LOG, 'log_end_offset': len(raw),
            'synopsis_sha256': rendered['synopsis_sha256'],
        }]}}]
        if commit:
            self.git('add', LOG, VIEW)
            self.git('commit', '-qm', 'Unsigned disposable audit fixture')

    def outcome(self, controller=CANDIDATE):
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            try:
                value = controller._guard_audit_pair_operation(str(self.root), self.state)
                return 0, value, errors.getvalue()
            except SystemExit as exc:
                return exc.code, None, errors.getvalue()

    def refused(self):
        code, _, error = self.outcome()
        self.assertEqual(code, 2, error)

    def test_fresh_absent_pair_still_passes(self):
        self.assertEqual(self.outcome()[0], 0)

    def test_fresh_unreceipted_pair_still_refuses(self):
        self.pair()
        self.state['steps'] = []
        self.refused()

    def test_valid_untracked_pair_preserves_the_existing_result(self):
        self.pair()
        self.assertEqual(self.outcome()[0], 0)

    def test_committed_receipted_pair_is_admitted(self):
        self.pair(commit=True)
        self.assertEqual(self.git('status', '--porcelain=v1'), b'')
        code, record, error = self.outcome()
        self.assertEqual(code, 0, error)
        self.assertEqual(record['log_sha256'], hashlib.sha256(RAW).hexdigest())

    def test_committed_pair_with_untracked_extra_refuses(self):
        self.pair(commit=True)
        (self.root / 'foreign').write_bytes(b'extra\n')
        self.refused()

    def test_untracked_pair_with_third_dirty_row_refuses(self):
        self.pair()
        (self.root / 'foreign').write_bytes(b'extra\n')
        self.refused()

    def test_staged_pair_refuses(self):
        self.pair()
        self.git('add', LOG, VIEW)
        self.refused()

    def test_mixed_tracked_and_untracked_pair_refuses(self):
        self.pair()
        self.git('add', LOG)
        self.git('commit', '-qm', 'Only one audit member')
        self.refused()

    def test_ignored_untracked_pair_is_not_a_clean_committed_pair(self):
        self.pair()
        (self.root / '.git/info/exclude').write_text('audit/\n')
        self.assertEqual(self.git('status', '--porcelain=v1'), b'')
        self.refused()

    def test_receipt_mismatch_refuses_clean_committed_pair(self):
        self.pair(commit=True)
        self.state['steps'][0]['audit']['rounds'][0]['synopsis_sha256'] = '0' * 64
        self.refused()

    def test_missing_committed_member_refuses(self):
        self.pair(commit=True)
        (self.root / VIEW).unlink()
        self.refused()

    def test_missing_native_blob_is_not_supplied_by_worktree_bytes(self):
        self.pair(commit=True)
        oid = self.git('rev-parse', 'HEAD:' + LOG).decode().strip()
        blob = self.root / self.git(
            'rev-parse', '--git-path', f'objects/{oid[:2]}/{oid[2:]}'
        ).decode().strip()
        self.assertTrue(blob.is_file())
        blob.unlink()
        self.assertEqual(self.git('status', '--porcelain=v1'), b'')
        self.refused()

    def test_symlink_member_refuses_even_with_receipt_matching_target(self):
        self.pair()
        target = self.root / 'saved-log'
        shutil.move(self.root / LOG, target)
        (self.root / LOG).symlink_to(target)
        self.git('add', LOG, VIEW, 'saved-log')
        self.git('commit', '-qm', 'Symlink-shaped fixture')
        self.refused()

    def test_hardlinked_member_refuses(self):
        self.pair(commit=True)
        with tempfile.TemporaryDirectory(prefix='audit-custody-link-') as temporary:
            (Path(temporary) / 'alias').hardlink_to(self.root / LOG)
            self.refused()

    def test_assume_unchanged_cannot_hide_receipt_matching_worktree_drift(self):
        self.pair(commit=True)
        self.git('update-index', '--assume-unchanged', LOG, VIEW)
        self.pair(raw=RAW.replace(b'fixture=reviewed', b'changed=reviewed'))
        self.assertEqual(self.git('status', '--porcelain=v1'), b'')
        self.refused()

    def test_skip_worktree_cannot_hide_receipt_matching_worktree_drift(self):
        self.pair(commit=True)
        self.git('update-index', '--skip-worktree', LOG, VIEW)
        self.pair(raw=RAW.replace(b'fixture=reviewed', b'changed=reviewed'))
        self.assertEqual(self.git('status', '--porcelain=v1'), b'')
        self.refused()

    def test_index_change_is_not_hidden_by_native_head_matching_worktree(self):
        self.pair(commit=True)
        original_log = (self.root / LOG).read_bytes()
        (self.root / LOG).write_bytes(original_log + b'index-only\n')
        self.git('add', LOG)
        (self.root / LOG).write_bytes(original_log)
        self.refused()

    def test_head_movement_between_native_observations_refuses(self):
        self.pair(commit=True)
        original = CANDIDATE._guard_audit_native_pair
        calls = 0

        def move_after_first(*args, **kwargs):
            nonlocal calls
            result = original(*args, **kwargs)
            calls += 1
            if calls == 1:
                self.git('commit', '--allow-empty', '-qm', 'Move disposable HEAD')
            return result

        with mock.patch.object(CANDIDATE, '_guard_audit_native_pair', move_after_first):
            code, _, error = self.outcome()
        self.assertEqual(code, 2)
        self.assertIn('native pair changed during validation', error)
        self.assertEqual(calls, 2)

    def test_log_change_after_first_snapshot_refuses(self):
        self.pair(commit=True)
        original = CANDIDATE._guard_file_snapshot
        moved = False

        def change_after_capture(base, relative, *args, **kwargs):
            nonlocal moved
            result = original(base, relative, *args, **kwargs)
            if relative == LOG and not moved:
                moved = True
                path = Path(base, relative)
                path.write_bytes(path.read_bytes() + b'observed drift\n')
            return result

        with mock.patch.object(CANDIDATE, '_guard_file_snapshot', change_after_capture):
            code, _, error = self.outcome()
        self.assertEqual(code, 2)
        self.assertIn('audit pair changed during validation', error)

    def test_same_bytes_replacement_after_first_snapshot_refuses(self):
        self.pair(commit=True)
        original = CANDIDATE._guard_file_snapshot
        moved = False

        def replace_after_capture(base, relative, *args, **kwargs):
            nonlocal moved
            result = original(base, relative, *args, **kwargs)
            if relative == LOG and not moved:
                moved = True
                path = Path(base, relative)
                replacement = path.with_name('replacement')
                replacement.write_bytes(path.read_bytes())
                os.replace(replacement, path)
            return result

        with mock.patch.object(CANDIDATE, '_guard_file_snapshot', replace_after_capture):
            code, _, error = self.outcome()
        self.assertEqual(code, 2)
        self.assertIn('audit pair changed during validation', error)
