"""Focused controller-capsule export guards.

Step 2 exports exact controller bytes. It deliberately leaves relocation and
the clone-loss transition red for Step 3.
"""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import glob
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_hexctl import HEXCTL, LINTS_CLEAN, HexctlCase, hexctl_module


class HexctlCheckpointTests(HexctlCase):
    def controller_root(self):
        return Path(self.target) / ".hexaemeron"

    def state_ledger_bytes(self):
        root = self.controller_root()
        return (
            root.joinpath("state.json").read_bytes(),
            root.joinpath("ledger.jsonl").read_bytes(),
        )

    def to_post_push(self):
        self.to_steps(titles=("First", "Second"))
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.finish_step(1)

    def export(self, name, *, expect=0):
        destination = Path(self.dir) / name
        result = self.run_ctl(
            "checkpoint", "export", "--out", str(destination), expect=expect
        )
        payload = json.loads(result.stdout) if expect == 0 else None
        return destination, result, payload

    def assert_no_stage(self, destination):
        pattern = str(destination.parent / f".{destination.name}.stage-*")
        self.assertEqual([], glob.glob(pattern))

    def direct_environment(self):
        environment = dict(self.env)
        environment["FAKE_GIT_REFS"] = json.dumps(self.fake_refs)
        environment["FAKE_GIT_PARENTS"] = json.dumps(self.fake_parents)
        environment["FAKE_GH_PRS"] = json.dumps(self.fake_prs)
        return environment

    def direct_refusal(self, module, destination, *, destination_absent=True):
        stderr = StringIO()
        before = self.state_ledger_bytes()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as stopped:
                module.cmd_checkpoint_export(
                    SimpleNamespace(dir=self.target, out=str(destination))
                )
        self.assertEqual(2, stopped.exception.code)
        if destination_absent:
            self.assertFalse(destination.exists())
        self.assert_no_stage(destination)
        self.assertEqual(before, self.state_ledger_bytes())
        return stderr.getvalue()

    @staticmethod
    def tree_record(root):
        records = []
        for current, directories, files in os.walk(root):
            directories.sort()
            files.sort()
            current_path = Path(current)
            records.append(
                (
                    str(current_path.relative_to(root)) or ".",
                    "directory",
                    stat.S_IMODE(current_path.stat().st_mode),
                )
            )
            for name in files:
                path = current_path / name
                records.append(
                    (
                        str(path.relative_to(root)),
                        "file",
                        stat.S_IMODE(path.stat().st_mode),
                        path.read_bytes(),
                    )
                )
        return records

    def test_export_manifest_closes_the_controller_capsule(self):
        self.to_post_push()
        before = self.state_ledger_bytes()
        destination, _, result = self.export("capsule")
        self.assertEqual(before, self.state_ledger_bytes())

        manifest_bytes = destination.joinpath("MANIFEST.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        self.assertEqual(
            manifest_bytes,
            json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
            + b"\n",
        )
        self.assertEqual(
            set(manifest),
            {"schema", "controller", "boundary", "source", "resources", "files"},
        )
        self.assertEqual(manifest["schema"], "fiat-controller-checkpoint/v1")
        self.assertEqual(manifest["boundary"]["kind"], "post-push")
        self.assertEqual(manifest["boundary"]["next"]["do"], "implement")
        self.assertEqual(manifest["controller"]["name"], "hexctl")
        self.assertRegex(manifest["controller"]["version"], r"^fiat-v[0-9]+\.")

        controller = destination / "controller"
        expected = []
        for current, directories, files in os.walk(self.controller_root()):
            directories.sort()
            for name in sorted(files):
                if Path(current) == self.controller_root() and name == "lock":
                    continue
                path = Path(current) / name
                expected.append(
                    "controller/" + str(path.relative_to(self.controller_root()))
                )
        recorded = [entry["path"] for entry in manifest["files"]]
        self.assertEqual(sorted(expected), recorded)
        self.assertNotIn("controller/lock", recorded)
        for entry in manifest["files"]:
            path = destination / entry["path"]
            self.assertEqual(entry["bytes"], path.stat().st_size)
            self.assertEqual(
                entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )

        source = manifest["source"]
        self.assertEqual(
            source["state_sha256"], hashlib.sha256(before[0]).hexdigest()
        )
        self.assertEqual(
            source["ledger_sha256"], hashlib.sha256(before[1]).hexdigest()
        )
        self.assertEqual(
            result["manifest_sha256"], hashlib.sha256(manifest_bytes).hexdigest()
        )
        self.assertEqual(result["state_sha256"], source["state_sha256"])
        self.assertEqual(result["ledger_tail"], source["ledger_tail"])

        manifest_text = manifest_bytes.decode("utf-8")
        self.assertNotIn(self.target, manifest_text)
        for forbidden in (
            '"timestamp"',
            '"created_at"',
            '"origin"',
            '"worktree"',
            '"source_path"',
        ):
            self.assertNotIn(forbidden, manifest_text)

        for record in self.tree_record(destination):
            expected_mode = 0o700 if record[1] == "directory" else 0o600
            self.assertEqual(expected_mode, record[2], record[0])

    def test_export_is_deterministic_at_both_boundaries(self):
        self.to_post_push()
        before = self.state_ledger_bytes()
        post_a, _, _ = self.export("post-a")
        post_b, _, _ = self.export("post-b")
        self.assertEqual(self.tree_record(post_a), self.tree_record(post_b))
        self.assertEqual(before, self.state_ledger_bytes())

        self.run_ctl(
            "done",
            "implement",
            "--branch",
            self.step_branch(2),
            "--commit",
            "abc2",
        )
        self.run_ctl("config", "set", "audit.max_rounds", "1")
        self.run_ctl("audit-round", "--findings", "1", *LINTS_CLEAN)
        self.assertEqual("audit-verdict", self.next_json()["do"])
        before = self.state_ledger_bytes()
        audit_a, _, first = self.export("audit-a")
        audit_b, _, second = self.export("audit-b")
        self.assertEqual("audit-verdict", first["boundary"])
        self.assertEqual("audit-verdict", second["next"]["do"])
        self.assertEqual(self.tree_record(audit_a), self.tree_record(audit_b))
        self.assertEqual(before, self.state_ledger_bytes())

    def test_export_refuses_every_unaccepted_boundary(self):
        sequence = 0

        def refused(label):
            nonlocal sequence
            sequence += 1
            before = self.state_ledger_bytes()
            destination, result, _ = self.export(f"refused-{sequence}", expect=2)
            self.assertIn("allowed only", result.stderr, label)
            self.assertFalse(destination.exists(), label)
            self.assert_no_stage(destination)
            self.assertEqual(before, self.state_ledger_bytes(), label)

        self.init()
        refused("study")
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\npacket | state | compare\n```\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        refused("runbook")
        runbook = self.write(
            "runbook.md", "# Runbook\n\n## Step 1: One\n\n**Goal.** One.\n"
        )
        steps = self.write("steps.json", '["One"]\n')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "fixture")
        state = self.state()
        self.git("branch", self.step_branch(1, state))
        refused("implement")
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        refused("implement-after-receipt")
        self.run_ctl(
            "done",
            "implement",
            "--branch",
            self.step_branch(1),
            "--commit",
            "abc1",
        )
        refused("audit-before-round")
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        refused("close-audit")
        self.run_ctl("done", "audit")
        refused("prose")
        self.run_ctl(
            "done",
            "prose",
            "--files",
            "1",
            "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        refused("push")

    def test_a_later_controller_receipt_closes_the_post_push_boundary(self):
        self.to_post_push()
        self.export("accepted")
        self.run_ctl("record", "after_push", '"later action"')
        destination, result, _ = self.export("too-late", expect=2)
        self.assertIn("allowed only", result.stderr)
        self.assertFalse(destination.exists())

    def test_export_is_locked_without_mutating_state_or_ledger(self):
        self.to_post_push()
        before = self.state_ledger_bytes()
        holder, _, release = self.start_lock_holder(
            "checkpoint", command="cmd_checkpoint_export"
        )
        destination, result, _ = self.export("locked", expect=1)
        self.assertIn("another hexctl is holding this run", result.stderr)
        self.assertFalse(destination.exists())
        self.assertEqual(before, self.state_ledger_bytes())
        self.release_lock_holder(holder, release)

    def test_export_never_follows_a_replaced_lock_file(self):
        self.to_post_push()
        root = self.controller_root()
        lock = root / "lock"
        outside = Path(self.dir) / "outside-lock-target"
        outside.write_text("unchanged", encoding="utf-8")
        lock.unlink()
        lock.symlink_to(outside)
        destination, result, _ = self.export("lock-symlink", expect=1)
        self.assertIn("lock is not a safe regular file", result.stderr)
        self.assertEqual("unchanged", outside.read_text(encoding="utf-8"))
        self.assertFalse(destination.exists())

    def test_resource_limits_refuse_before_publish(self):
        self.to_post_push()
        root = self.controller_root()

        file_count = sum(
            1
            for current, _, files in os.walk(root)
            for name in files
            if not (Path(current) == root and name == "lock")
        )
        total = sum(
            (Path(current) / name).stat().st_size
            for current, _, files in os.walk(root)
            for name in files
            if not (Path(current) == root and name == "lock")
        )
        simple_limits = (
            ("files", {"CHECKPOINT_FILES_MAX": file_count - 1}, "too many"),
            ("total", {"CHECKPOINT_TOTAL_BYTES_MAX": total - 1}, "ceiling"),
            ("manifest", {"CHECKPOINT_MANIFEST_BYTES_MAX": 128}, "ceiling"),
        )
        for index, (label, patches, expected) in enumerate(simple_limits, 1):
            with self.subTest(limit=label):
                module = hexctl_module()
                with mock.patch.multiple(module, **patches):
                    error = self.direct_refusal(
                        module, Path(self.dir) / f"limit-{index}"
                    )
                self.assertIn(expected, error)

        oversized = root / "oversized.bin"
        with oversized.open("wb") as handle:
            handle.truncate(64 * 1024 * 1024 + 1)
        try:
            error = self.direct_refusal(hexctl_module(), Path(self.dir) / "limit-file")
            self.assertIn("byte ceiling", error)
        finally:
            oversized.unlink()

        long_root = root
        for index in range(6):
            long_root = long_root / ((chr(ord("a") + index)) * 200)
            long_root.mkdir()
        long_file = long_root / "value"
        long_file.write_text("x", encoding="utf-8")
        try:
            error = self.direct_refusal(hexctl_module(), Path(self.dir) / "limit-path")
            self.assertIn("path exceeds", error)
        finally:
            shutil.rmtree(root / ("a" * 200))

        empty = root / "bounded-directory"
        empty.mkdir()
        try:
            module = hexctl_module()
            with mock.patch.object(module, "CHECKPOINT_DIRECTORIES_MAX", 1):
                error = self.direct_refusal(module, Path(self.dir) / "limit-directory")
            self.assertIn("too many directories", error)
        finally:
            empty.rmdir()

    def test_file_count_cap_stops_directory_enumeration(self):
        source = Path(self.dir) / "enumeration-source"
        source.mkdir()
        for index in range(12):
            source.joinpath(f"entry-{index:02d}").write_text("x", encoding="utf-8")

        module = hexctl_module()
        real_scandir = os.scandir
        consumed = 0

        class CountingScandir:
            def __init__(self, path):
                self.iterator = real_scandir(path)

            def __enter__(self):
                self.iterator.__enter__()
                return self

            def __exit__(self, *args):
                return self.iterator.__exit__(*args)

            def __iter__(self):
                return self

            def __next__(self):
                nonlocal consumed
                entry = next(self.iterator)
                consumed += 1
                return entry

        stderr = StringIO()
        with mock.patch.object(module, "CHECKPOINT_FILES_MAX", 2):
            with mock.patch.object(module.os, "scandir", CountingScandir):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    module._checkpoint_snapshot(str(source), None)

        self.assertIn("too many files", stderr.getvalue())
        self.assertEqual(3, consumed)

    def test_hostile_controller_entries_refuse_without_echo_or_mutation(self):
        self.to_post_push()
        root = self.controller_root()
        specimens = (
            ("symlink", lambda path: path.symlink_to("state.json")),
            ("fifo", lambda path: os.mkfifo(path)),
            ("hardlink", lambda path: os.link(root / "state.json", path)),
            (
                "directory-symlink",
                lambda path: path.symlink_to(root, target_is_directory=True),
            ),
        )
        for index, (kind, create) in enumerate(specimens, 1):
            with self.subTest(kind=kind):
                path = root / f"ghp_SUPER_SECRET_{kind}"
                create(path)
                try:
                    before = self.state_ledger_bytes()
                    destination, result, _ = self.export(
                        f"hostile-{index}", expect=2
                    )
                    self.assertFalse(destination.exists())
                    self.assertNotIn("ghp_SUPER_SECRET", result.stderr)
                    self.assertEqual(before, self.state_ledger_bytes())
                finally:
                    path.unlink(missing_ok=True)

    def test_duplicate_state_and_ledger_keys_refuse(self):
        self.to_post_push()
        root = self.controller_root()
        state_path = root / "state.json"
        ledger_path = root / "ledger.jsonl"
        original_state = state_path.read_text(encoding="utf-8")
        original_ledger = ledger_path.read_text(encoding="utf-8")

        state_path.write_text(
            original_state.replace("{", '{"version":1,', 1), encoding="utf-8"
        )
        try:
            destination, result, _ = self.export("duplicate-state", expect=2)
            self.assertIn("strict UTF-8 JSON", result.stderr)
            self.assertFalse(destination.exists())
        finally:
            state_path.write_text(original_state, encoding="utf-8")

        lines = original_ledger.splitlines()
        last = json.loads(lines[-1])
        lines[-1] = lines[-1].replace(
            "{", json.dumps({"event": last["event"]})[:-1] + ",", 1
        )
        ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        try:
            destination, result, _ = self.export("duplicate-ledger", expect=2)
            self.assertIn("strict UTF-8 JSON", result.stderr)
            self.assertFalse(destination.exists())
        finally:
            ledger_path.write_text(original_ledger, encoding="utf-8")

    def test_moving_input_refuses_before_publication(self):
        self.to_post_push()
        moving = self.controller_root() / "moving"
        moving.write_bytes(b"before")
        module = hexctl_module()
        original = module._checkpoint_snapshot
        changed = False

        def move_after_capture(source, destination):
            nonlocal changed
            inventory = original(source, destination)
            if destination is not None and not changed:
                moving.write_bytes(b"after")
                changed = True
            return inventory

        with mock.patch.object(module, "_checkpoint_snapshot", move_after_capture):
            error = self.direct_refusal(
                module, Path(self.dir) / "moving-capsule"
            )
        self.assertIn("changed before publication", error)

    def test_interruption_before_atomic_publish_leaves_no_capsule(self):
        self.to_post_push()
        module = hexctl_module()
        destination = Path(self.dir) / "interrupted"
        before = self.state_ledger_bytes()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_atomic_publish",
                side_effect=RuntimeError("cut"),
            ):
                with redirect_stdout(StringIO()), self.assertRaisesRegex(
                    RuntimeError, "cut"
                ):
                    module.cmd_checkpoint_export(
                        SimpleNamespace(dir=self.target, out=str(destination))
                    )
        self.assertFalse(destination.exists())
        self.assert_no_stage(destination)
        self.assertEqual(before, self.state_ledger_bytes())

    def test_occupied_and_racing_destinations_are_never_replaced(self):
        self.to_post_push()
        occupied = Path(self.dir) / "occupied"
        occupied.mkdir()
        marker = occupied / "owned"
        marker.write_text("keep", encoding="utf-8")
        before = self.state_ledger_bytes()
        result = self.run_ctl(
            "checkpoint", "export", "--out", str(occupied), expect=2
        )
        self.assertIn("occupied", result.stderr)
        self.assertEqual("keep", marker.read_text(encoding="utf-8"))
        self.assertEqual(before, self.state_ledger_bytes())

        module = hexctl_module()
        raced = Path(self.dir) / "raced"
        original = module._checkpoint_atomic_publish

        def occupy_then_publish(stage, destination):
            Path(destination).mkdir()
            return original(stage, destination)

        with mock.patch.object(
            module, "_checkpoint_atomic_publish", occupy_then_publish
        ):
            error = self.direct_refusal(
                module, raced, destination_absent=False
            )
        self.assertIn("became occupied", error)
        self.assertTrue(raced.is_dir())
        self.assertEqual([], list(raced.iterdir()))

    def test_replaced_output_parent_cannot_redirect_publication(self):
        self.to_post_push()
        parent = Path(self.dir) / "output-parent"
        moved_parent = Path(self.dir) / "moved-output-parent"
        alternate = Path(self.dir) / "alternate-parent"
        parent.mkdir()
        alternate.mkdir()
        destination = parent / "capsule"

        module = hexctl_module()
        original_refs = module._checkpoint_refs
        rebound = False

        def rebind_after_validation(base_dir, state):
            nonlocal rebound
            refs = original_refs(base_dir, state)
            if not rebound:
                parent.rename(moved_parent)
                parent.symlink_to(alternate, target_is_directory=True)
                rebound = True
            return refs

        before = self.state_ledger_bytes()
        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(module, "_checkpoint_refs", rebind_after_validation):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    module.cmd_checkpoint_export(
                        SimpleNamespace(dir=self.target, out=str(destination))
                    )

        self.assertIn("parent changed", stderr.getvalue())
        self.assertFalse(alternate.joinpath("capsule").exists())
        self.assertFalse(moved_parent.joinpath("capsule").exists())
        self.assertEqual(before, self.state_ledger_bytes())

    def test_pending_transaction_and_unsafe_output_parents_refuse(self):
        self.to_post_push()
        pending = self.controller_root() / "state.json.tmp"
        pending.write_text("pending", encoding="utf-8")
        try:
            destination, result, _ = self.export("pending", expect=2)
            self.assertIn("pending controller transaction", result.stderr)
            self.assertFalse(destination.exists())
        finally:
            pending.unlink()

        inside = self.controller_root() / "capsule"
        result = self.run_ctl(
            "checkpoint", "export", "--out", str(inside), expect=2
        )
        self.assertIn("cannot enter controller state", result.stderr)
        self.assertFalse(inside.exists())

        real_parent = Path(self.dir) / "real-parent"
        real_parent.mkdir()
        linked_parent = Path(self.dir) / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        linked = linked_parent / "capsule"
        result = self.run_ctl(
            "checkpoint", "export", "--out", str(linked), expect=2
        )
        self.assertIn("non-symlink directory", result.stderr)
        self.assertFalse(real_parent.joinpath("capsule").exists())

    def test_export_keeps_clone_local_recovery_explicitly_unavailable(self):
        self.init()
        worktree = self.target
        shutil.rmtree(worktree)
        result = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "next"],
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("no longer there", result.stderr)
        self.assertIn("Restore it", result.stderr)


if __name__ == "__main__":
    unittest.main()
