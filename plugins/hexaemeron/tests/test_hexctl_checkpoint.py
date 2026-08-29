"""Focused controller-capsule export and same-ledger restore guards."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import glob
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tracemalloc
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_hexctl import HEXCTL, LINTS_CLEAN, HexctlCase, hexctl_module


FIAT_SKILL = Path(__file__).resolve().parents[1] / "skills" / "fiat" / "SKILL.md"


class HexctlCheckpointTests(HexctlCase):
    def test_public_recovery_routes_checkpoint_arrivals_before_fresh_init(self):
        fiat = FIAT_SKILL.read_text(encoding="utf-8")
        checkpoint = fiat.index("checkpoint zip")
        active_state = fiat.index("If `.hexaemeron/state.json` exists")
        fresh_init = fiat.index("Otherwise: say exactly `Let there be light.`")
        self.assertLess(
            checkpoint,
            active_state,
            "checkpoint recovery must be selected before active-state resume",
        )
        self.assertLess(
            active_state,
            fresh_init,
            "active-state resume must be selected before fresh initialization",
        )

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

    def to_post_push_with_controller_sources(self):
        self.init()
        study = self.write(
            ".hexaemeron/study.md",
            "# Study\n\n```risk-register\npacket | boundary | check\n```\n",
        )
        self.run_ctl(
            "done",
            "study",
            "--artifact",
            study,
            "--skills",
            "hexaemeron:imprimatur",
        )
        runbook = self.write(
            ".hexaemeron/runbook.md",
            "# Runbook\n\n"
            "## Step 1: First\n\n**Goal.** First.\n\n"
            "## Step 2: Second\n\n**Goal.** Second.\n",
        )
        steps = self.write(
            ".hexaemeron/steps.json", json.dumps(["First", "Second"])
        )
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        state = self.state()
        for step in state["steps"]:
            self.git("branch", self.step_branch(step["n"], state))
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.finish_step(1)

    @staticmethod
    def rewrite_capsule_state(capsule, change):
        module = hexctl_module()
        controller = capsule / "controller"
        state_path = controller / "state.json"
        ledger_path = controller / "ledger.jsonl"
        state = json.loads(state_path.read_bytes())
        change(state)
        state_path.write_bytes(
            json.dumps(state, indent=2, sort_keys=False).encode("utf-8") + b"\n"
        )

        lines = ledger_path.read_bytes().splitlines()
        last = json.loads(lines[-1])
        last["state"] = module.state_fingerprint(state)
        body = {
            key: last[key] for key in ("ts", "event", "data", "prev", "state")
        }
        last["hash"] = hashlib.sha256(module.canonical(body).encode()).hexdigest()
        ledger = (
            b"\n".join(lines[:-1])
            + (b"\n" if lines[:-1] else b"")
            + json.dumps(last, sort_keys=True).encode("utf-8")
            + b"\n"
        )
        ledger_path.write_bytes(ledger)

        inventory = module._checkpoint_snapshot(str(controller), None)
        manifest_path = capsule / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_bytes())
        count, tail = module._checkpoint_ledger(ledger, state)
        state_bytes = state_path.read_bytes()
        manifest["source"] = {
            "state_sha256": hashlib.sha256(state_bytes).hexdigest(),
            "state_fingerprint": module.state_fingerprint(state),
            "ledger_sha256": hashlib.sha256(ledger).hexdigest(),
            "ledger_entries": count,
            "ledger_tail": tail,
        }
        manifest["files"] = inventory
        manifest["resources"]["files"] = len(inventory)
        manifest["resources"]["bytes"] = sum(item["bytes"] for item in inventory)
        payload = module.canonical(manifest).encode("utf-8") + b"\n"
        manifest_path.write_bytes(payload)
        return hashlib.sha256(payload).hexdigest()

    def export(self, name, *, expect=0):
        destination = Path(self.dir) / name
        result = self.run_ctl(
            "checkpoint", "export", "--out", str(destination), expect=expect
        )
        payload = json.loads(result.stdout) if expect == 0 else None
        return destination, result, payload

    def fresh_origin_for(self, capsule):
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        origin = Path(home.name) / "origin"
        subprocess.run(
            ["git", "clone", "-q", self.dir, str(origin)],
            check=True,
            capture_output=True,
        )
        manifest = json.loads(capsule.joinpath("MANIFEST.json").read_bytes())
        for ref in manifest["boundary"]["refs"]:
            if ref == "main" or re.fullmatch(r"[0-9a-f]{40}", ref):
                continue
            subprocess.run(
                ["git", "branch", ref, f"origin/{ref}"],
                cwd=origin,
                check=True,
                capture_output=True,
            )
        return origin, manifest

    def restore_into(self, origin, capsule, digest, *, expect=0, environment=None):
        result = subprocess.run(
            [
                sys.executable,
                HEXCTL,
                "--dir",
                str(origin),
                "checkpoint",
                "restore",
                "--from",
                str(capsule),
                "--manifest-sha256",
                digest,
            ],
            capture_output=True,
            text=True,
            env=environment or self.direct_environment(),
        )
        self.assertEqual(expect, result.returncode, result.stderr)
        return result

    @staticmethod
    def restored_worktree(origin):
        return Path(
            origin.joinpath(".hexaemeron", "worktree")
            .read_text(encoding="utf-8")
            .strip()
        )

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
        self.record_legacy_config("audit.max_rounds", 1)
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

        module = hexctl_module()
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            module._checkpoint_json(b'{"value":NaN}', "state")
        self.assertIn("strict UTF-8 JSON", stderr.getvalue())

        stderr = StringIO()
        nested = b"[" * 50_000 + b"0" + b"]" * 50_000
        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            module._checkpoint_json(nested, "state")
        self.assertIn("strict UTF-8 JSON", stderr.getvalue())

    def test_moving_input_refuses_before_publication(self):
        self.to_post_push()
        moving = self.controller_root() / "moving"
        moving.write_bytes(b"before")
        module = hexctl_module()
        original = module._checkpoint_snapshot
        changed = False

        def move_after_capture(source, destination, **kwargs):
            nonlocal changed
            inventory = original(source, destination, **kwargs)
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

    def test_replaced_private_stage_is_not_deleted(self):
        self.to_post_push()
        module = hexctl_module()
        destination = Path(self.dir) / "stage-replaced"
        detached_stage = Path(self.dir) / "detached-stage"
        original_snapshot = module._checkpoint_snapshot
        replacement_marker = None

        def replace_stage_after_capture(source, target, **kwargs):
            nonlocal replacement_marker
            inventory = original_snapshot(source, target, **kwargs)
            if target is not None and replacement_marker is None:
                stage = Path(target).parent
                stage.rename(detached_stage)
                stage.mkdir(mode=0o700)
                replacement_marker = stage / "unowned-marker"
                replacement_marker.write_text("must survive", encoding="utf-8")
            return inventory

        before = self.state_ledger_bytes()
        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module, "_checkpoint_snapshot", replace_stage_after_capture
            ):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    module.cmd_checkpoint_export(
                        SimpleNamespace(dir=self.target, out=str(destination))
                    )

        self.assertIn("checkpoint", stderr.getvalue())
        self.assertIsNotNone(replacement_marker)
        self.assertTrue(replacement_marker.exists())
        self.assertTrue(detached_stage.exists())
        self.assertFalse(destination.exists())
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

    def test_export_refuses_a_non_appendable_ledger_prefix(self):
        self.to_post_push()
        ledger_path = self.controller_root() / "ledger.jsonl"
        ledger_path.write_bytes(ledger_path.read_bytes().removesuffix(b"\n"))

        destination, result, _ = self.export("non-appendable", expect=2)
        self.assertIn("appendable exact prefix", result.stderr)
        self.assertFalse(destination.exists())
        self.assert_no_stage(destination)

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

    def test_restore_after_source_clone_loss(self):
        self.to_post_push()
        source_state, source_ledger = self.state_ledger_bytes()
        capsule, _, exported = self.export("capsule")
        expected_next = json.loads(
            capsule.joinpath("MANIFEST.json").read_bytes()
        )["boundary"]["next"]

        source_worktree = Path(self.target)
        shutil.rmtree(source_worktree)
        fresh_origin, _ = self.fresh_origin_for(capsule)
        result = self.restore_into(
            fresh_origin, capsule, exported["manifest_sha256"]
        )
        restored = self.restored_worktree(fresh_origin)
        state = json.loads(restored.joinpath(".hexaemeron", "state.json").read_bytes())
        ledger = restored.joinpath(".hexaemeron", "ledger.jsonl").read_bytes()
        self.assertEqual(
            str(fresh_origin.resolve()), state["config"]["git"]["origin"]
        )
        self.assertEqual(
            str(restored.resolve()), state["config"]["git"]["worktree"]
        )
        self.assertTrue(ledger.startswith(source_ledger))
        self.assertEqual(
            len(source_ledger.splitlines()) + 1,
            len(ledger.splitlines()),
        )
        self.assertNotEqual(source_state, state)
        self.assertEqual("checkpoint:restore", json.loads(ledger.splitlines()[-1])["event"])
        self.assertEqual(expected_next, json.loads(result.stdout)["next"])

    def test_restore_controller_local_sources_survive_clone_loss(self):
        self.to_post_push_with_controller_sources()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        expected_study = capsule.joinpath("controller", "study.md").read_bytes()
        expected_runbook = capsule.joinpath("controller", "runbook.md").read_bytes()
        shutil.rmtree(self.target)

        self.restore_into(origin, capsule, exported["manifest_sha256"])
        restored = self.restored_worktree(origin)
        self.assertEqual(
            expected_study,
            restored.joinpath(".hexaemeron", "study.md").read_bytes(),
        )
        self.assertEqual(
            expected_runbook,
            restored.joinpath(".hexaemeron", "runbook.md").read_bytes(),
        )

    def test_restore_receipt_path_traversal_refuses_before_marker(self):
        self.to_post_push()
        capsule, _, _ = self.export("capsule")
        outside = Path(self.dir) / "outside-proof"
        outside.write_text("outside controller boundary\n", encoding="utf-8")

        def change(state):
            state["receipts"]["study"]["artifact"] = (
                ".hexaemeron/../../outside-proof"
            )
            state["receipts"]["study"]["sha256"] = hashlib.sha256(
                outside.read_bytes()
            ).hexdigest()

        digest = self.rewrite_capsule_state(capsule, change)
        origin, _ = self.fresh_origin_for(capsule)
        refused = self.restore_into(origin, capsule, digest, expect=2)
        self.assertIn("unsafe", refused.stderr)
        self.assertFalse(origin.joinpath(".hexaemeron").exists())

    def test_restore_preserves_prefix_and_appends_one_receipt(self):
        self.to_post_push()
        _, source_ledger = self.state_ledger_bytes()
        capsule, _, exported = self.export("capsule")
        origin, manifest = self.fresh_origin_for(capsule)

        result = self.restore_into(origin, capsule, exported["manifest_sha256"])
        restored = self.restored_worktree(origin)
        ledger = restored.joinpath(".hexaemeron", "ledger.jsonl").read_bytes()
        self.assertEqual(source_ledger, ledger[: len(source_ledger)])
        self.assertEqual(
            len(source_ledger.splitlines()) + 1, len(ledger.splitlines())
        )
        receipt = json.loads(ledger.splitlines()[-1])
        self.assertEqual("checkpoint:restore", receipt["event"])
        self.assertEqual(manifest["source"]["ledger_tail"], receipt["prev"])
        self.assertEqual(exported["manifest_sha256"], receipt["data"]["manifest_sha256"])
        self.assertEqual(manifest["boundary"]["refs"], receipt["data"]["refs"])
        self.assertEqual(receipt["hash"], json.loads(result.stdout)["ledger_tail"])

    def test_restore_relocates_only_controller_paths(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        imported = json.loads(capsule.joinpath("controller", "state.json").read_bytes())

        self.restore_into(origin, capsule, exported["manifest_sha256"])
        restored = self.restored_worktree(origin)
        relocated = json.loads(
            restored.joinpath(".hexaemeron", "state.json").read_bytes()
        )
        expected = json.loads(json.dumps(imported))
        expected.pop("origin", None)
        expected.pop("worktree", None)
        expected["config"]["git"]["origin"] = str(origin.resolve())
        expected["config"]["git"]["worktree"] = str(restored.resolve())
        self.assertEqual(expected, relocated)

        source_root = capsule / "controller"
        target_root = restored / ".hexaemeron"
        for current, directories, files in os.walk(source_root):
            directories.sort()
            for name in sorted(files):
                relative = (Path(current) / name).relative_to(source_root)
                if str(relative) in ("state.json", "ledger.jsonl"):
                    continue
                self.assertEqual(
                    (Path(current) / name).read_bytes(),
                    target_root.joinpath(relative).read_bytes(),
                    str(relative),
                )
        receipt = json.loads(
            target_root.joinpath("ledger.jsonl").read_bytes().splitlines()[-1]
        )["data"]
        self.assertEqual(
            hexctl_module().state_fingerprint(relocated),
            receipt["relocated_state_fingerprint"],
        )

    def test_restore_ref_substitution_and_replay_refuse_without_rewrite(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, manifest = self.fresh_origin_for(capsule)
        substituted = dict(self.fake_refs)
        ref = next(iter(manifest["boundary"]["refs"]))
        substituted[ref] = "9" * 40
        environment = self.direct_environment()
        environment["FAKE_GIT_REFS"] = json.dumps(substituted)

        refused = self.restore_into(
            origin,
            capsule,
            exported["manifest_sha256"],
            expect=2,
            environment=environment,
        )
        self.assertIn("refs do not match", refused.stderr)
        self.assertFalse(origin.joinpath(".hexaemeron").exists())

        self.restore_into(origin, capsule, exported["manifest_sha256"])
        restored = self.restored_worktree(origin)
        before = restored.joinpath(".hexaemeron", "ledger.jsonl").read_bytes()
        replay = self.restore_into(
            origin, capsule, exported["manifest_sha256"], expect=2
        )
        self.assertIn("already occupied", replay.stderr)
        self.assertEqual(
            before, restored.joinpath(".hexaemeron", "ledger.jsonl").read_bytes()
        )

    def test_restore_hostile_capsule_and_digest_refuse_before_marker(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        mismatch = self.restore_into(origin, capsule, "0" * 64, expect=2)
        self.assertIn("digest does not match", mismatch.stderr)
        self.assertFalse(origin.joinpath(".hexaemeron").exists())

        hostile = capsule.joinpath("controller", "hostile-link")
        hostile.symlink_to("state.json")
        refused = self.restore_into(
            origin, capsule, exported["manifest_sha256"], expect=2
        )
        self.assertIn("special or linked", refused.stderr)
        self.assertFalse(origin.joinpath(".hexaemeron").exists())

    def test_restore_manifest_shape_and_caps_refuse_before_marker(self):
        self.to_post_push()
        capsule, _, _ = self.export("capsule")
        module = hexctl_module()

        duplicate = Path(self.dir) / "duplicate-manifest"
        shutil.copytree(capsule, duplicate)
        manifest_path = duplicate / "MANIFEST.json"
        malformed = manifest_path.read_bytes().replace(
            b'{"boundary"', b'{"schema":"duplicate","boundary"', 1
        )
        manifest_path.write_bytes(malformed)
        origin, _ = self.fresh_origin_for(capsule)
        refused = self.restore_into(
            origin,
            duplicate,
            hashlib.sha256(malformed).hexdigest(),
            expect=2,
        )
        self.assertIn("strict UTF-8 JSON", refused.stderr)
        self.assertFalse(origin.joinpath(".hexaemeron").exists())

        capped = Path(self.dir) / "false-cap"
        shutil.copytree(capsule, capped)
        manifest_path = capped / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["resources"]["limits"]["files"] += 1
        payload = (
            json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
            + b"\n"
        )
        manifest_path.write_bytes(payload)
        origin, _ = self.fresh_origin_for(capsule)
        refused = self.restore_into(
            origin,
            capped,
            hashlib.sha256(payload).hexdigest(),
            expect=2,
        )
        self.assertIn("resource limits", refused.stderr)
        self.assertFalse(origin.joinpath(".hexaemeron").exists())

        mixed = Path(self.dir) / "mixed-inventory"
        shutil.copytree(capsule, mixed)
        manifest_path = mixed / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["files"][0]["path"] = 1
        payload = (
            json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
            + b"\n"
        )
        manifest_path.write_bytes(payload)
        origin, _ = self.fresh_origin_for(capsule)
        refused = self.restore_into(
            origin,
            mixed,
            hashlib.sha256(payload).hexdigest(),
            expect=2,
        )
        self.assertNotIn("Traceback", refused.stderr)
        self.assertFalse(origin.joinpath(".hexaemeron").exists())

        boolean_version = Path(self.dir) / "boolean-state-version"
        shutil.copytree(capsule, boolean_version)
        manifest_path = boolean_version / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["controller"]["state_version"] = True
        payload = module.canonical(manifest).encode("utf-8") + b"\n"
        manifest_path.write_bytes(payload)
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            module._checkpoint_restore_capsule(
                str(boolean_version), hashlib.sha256(payload).hexdigest()
            )
        self.assertIn("controller identity", stderr.getvalue())

    def test_restore_blank_ledger_padding_stays_within_streaming_memory_bound(self):
        self.to_post_push()
        capsule, _, _ = self.export("capsule")
        module = hexctl_module()
        controller = capsule / "controller"
        ledger_path = controller / "ledger.jsonl"
        ledger = b"\n" * (2 * 1024 * 1024) + ledger_path.read_bytes()
        ledger_path.write_bytes(ledger)
        state = json.loads(controller.joinpath("state.json").read_bytes())
        inventory = module._checkpoint_snapshot(str(controller), None)
        manifest_path = capsule / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_bytes())
        count, tail = module._checkpoint_ledger(ledger, state)
        manifest["source"]["ledger_sha256"] = hashlib.sha256(ledger).hexdigest()
        manifest["source"]["ledger_entries"] = count
        manifest["source"]["ledger_tail"] = tail
        manifest["files"] = inventory
        manifest["resources"]["files"] = len(inventory)
        manifest["resources"]["bytes"] = sum(
            item["bytes"] for item in inventory
        )
        payload = module.canonical(manifest).encode("utf-8") + b"\n"
        manifest_path.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()

        tracemalloc.start()
        try:
            module._checkpoint_restore_capsule(str(capsule), digest)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLess(
            peak,
            8 * 1024 * 1024,
            f"blank-ledger verification peaked at {peak} bytes",
        )

    def test_restore_rejects_unmanifested_lock_before_marker(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        capsule.joinpath("controller", "lock").write_text(
            "unmanifested\n", encoding="utf-8"
        )
        origin, _ = self.fresh_origin_for(capsule)
        refused = self.restore_into(
            origin, capsule, exported["manifest_sha256"], expect=2
        )
        self.assertIn("lock", refused.stderr)
        self.assertFalse(origin.joinpath(".hexaemeron").exists())

    def test_restore_output_caps_refuse_before_stage_write(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        module = hexctl_module()
        imported = json.loads(
            capsule.joinpath("controller", "state.json").read_bytes()
        )
        ledger_prefix = capsule.joinpath(
            "controller", "ledger.jsonl"
        ).read_bytes()
        manifest = json.loads(capsule.joinpath("MANIFEST.json").read_bytes())
        origin = str(Path(self.dir) / "fresh-origin")
        worktree = str(Path(self.dir) / "restored-worktree")
        relocated, receipt = module._checkpoint_restore_state(
            imported,
            origin,
            worktree,
            manifest,
            exported["manifest_sha256"],
        )
        stage = Path(self.dir) / "bounded-output-stage"
        stage.mkdir()

        stderr = StringIO()
        with mock.patch.object(module, "SOURCE_BYTES_MAX", 1):
            with redirect_stderr(stderr), self.assertRaises(SystemExit):
                module._checkpoint_restore_write_files(
                    str(stage), relocated, ledger_prefix, receipt
                )
        self.assertIn("state exceeds", stderr.getvalue())
        self.assertEqual([], list(stage.iterdir()))

        stderr = StringIO()
        with mock.patch.object(
            module, "CHECKPOINT_FILE_BYTES_MAX", len(ledger_prefix)
        ):
            with redirect_stderr(stderr), self.assertRaises(SystemExit):
                module._checkpoint_restore_write_files(
                    str(stage), relocated, ledger_prefix, receipt
                )
        self.assertIn("ledger exceeds", stderr.getvalue())
        self.assertEqual([], list(stage.iterdir()))

    def test_restore_occupied_paths_are_never_replaced(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, manifest = self.fresh_origin_for(capsule)
        state = json.loads(capsule.joinpath("controller", "state.json").read_bytes())
        run_branch = state["run_branch"].replace("/", "-")
        home = origin / "tmp" / "fiat"
        home.mkdir(parents=True)
        home.joinpath(".gitignore").write_text("*\n", encoding="utf-8")
        occupied = home / run_branch
        occupied.mkdir(parents=True)
        sentinel = occupied / "sentinel"
        sentinel.write_text("unowned\n", encoding="utf-8")

        refused = self.restore_into(
            origin, capsule, exported["manifest_sha256"], expect=2
        )
        self.assertIn("already occupied", refused.stderr)
        self.assertEqual("unowned\n", sentinel.read_text(encoding="utf-8"))
        self.assertFalse(origin.joinpath(".hexaemeron").exists())
        self.assertEqual(manifest["boundary"]["refs"], exported["refs"])

    def test_restore_moved_marker_root_cannot_redirect_writes(self):
        self.to_post_push()
        capsule, _, _ = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        imported = json.loads(
            capsule.joinpath("controller", "state.json").read_bytes()
        )
        module = hexctl_module()
        root = origin / ".hexaemeron"
        detached = origin / ".hexaemeron-detached"
        outside = Path(self.dir) / "outside-marker-root"
        outside.mkdir()
        original_mkdir = module.os.mkdir
        moved = False

        def move_root_after_mkdir(name, mode=0o777, *args, **kwargs):
            nonlocal moved
            result = original_mkdir(name, mode, *args, **kwargs)
            candidate = Path(name)
            if not candidate.is_absolute():
                candidate = origin / candidate
            if not moved and candidate == root:
                moved = True
                os.rename(root, detached)
                os.symlink(outside, root, target_is_directory=True)
            return result

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module.os, "mkdir", side_effect=move_root_after_mkdir
            ):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    module._checkpoint_restore_marker(
                        str(origin), imported, "1" * 64
                    )
        self.assertIn("marker could not be published", stderr.getvalue())
        self.assertEqual([], list(outside.iterdir()))

    def test_restore_moved_worktree_home_cannot_redirect_writes(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        imported = json.loads(
            capsule.joinpath("controller", "state.json").read_bytes()
        )
        module = hexctl_module()
        home = origin / "tmp" / "fiat"
        outside = Path(self.dir) / "outside-worktree-home"
        outside.mkdir()
        original_marker = module._checkpoint_restore_marker

        def replace_home_after_marker(*args):
            result = original_marker(*args)
            home.parent.mkdir(parents=True, exist_ok=True)
            home.symlink_to(outside, target_is_directory=True)
            return result

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_marker",
                side_effect=replace_home_after_marker,
            ):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    module.cmd_checkpoint_restore(
                        SimpleNamespace(
                            dir=str(origin),
                            source=str(capsule),
                            manifest_sha256=exported["manifest_sha256"],
                        )
                    )
        self.assertEqual([], list(outside.iterdir()))

    def test_restore_moved_private_stage_cannot_redirect_writes(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        imported = json.loads(
            capsule.joinpath("controller", "state.json").read_bytes()
        )
        module = hexctl_module()
        worktree, stage_name, _ = module._checkpoint_restore_marker_paths(
            str(origin), imported, exported["manifest_sha256"]
        )
        stage = Path(stage_name)
        detached = Path(f"{stage_name}-detached")
        outside = Path(self.dir) / "outside-restore-stage"
        outside.mkdir()
        original_state = module._checkpoint_restore_state

        def replace_stage_before_write(*args):
            result = original_state(*args)
            stage.rename(detached)
            stage.symlink_to(outside, target_is_directory=True)
            return result

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_state",
                side_effect=replace_stage_before_write,
            ):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    module.cmd_checkpoint_restore(
                        SimpleNamespace(
                            dir=str(origin),
                            source=str(capsule),
                            manifest_sha256=exported["manifest_sha256"],
                        )
                    )
        self.assertEqual([], list(outside.iterdir()))

    def test_restore_moving_capsule_refuses_before_marker(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        original = module._checkpoint_snapshot
        changed = False

        def move_after_inventory(source, destination, **kwargs):
            nonlocal changed
            inventory = original(source, destination, **kwargs)
            if destination is None and not changed:
                changed = True
                Path(source, ".gitignore").write_text("changed\n", encoding="utf-8")
            return inventory

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(module, "_checkpoint_snapshot", move_after_inventory):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    module.cmd_checkpoint_restore(
                        SimpleNamespace(
                            dir=str(origin),
                            source=str(capsule),
                            manifest_sha256=exported["manifest_sha256"],
                        )
                    )
        self.assertIn("changed during verification", stderr.getvalue())
        self.assertFalse(origin.joinpath(".hexaemeron").exists())

    def test_restore_staged_read_rejects_named_file_substitution(self):
        module = hexctl_module()
        target = Path(self.dir) / "staged-state.json"
        replacement = Path(self.dir) / "replacement-state.json"
        detached = Path(self.dir) / "detached-state.json"
        target.write_bytes(b"expected\n")
        replacement.write_bytes(b"substituted\n")
        original_open = module.os.open
        moved = False

        def replace_after_open(name, flags, *args, **kwargs):
            nonlocal moved
            descriptor = original_open(name, flags, *args, **kwargs)
            if not moved and os.fspath(name) == os.fspath(target):
                moved = True
                os.rename(target, detached)
                os.rename(replacement, target)
            return descriptor

        stderr = StringIO()
        with mock.patch.object(
            module.os, "open", side_effect=replace_after_open
        ):
            with redirect_stderr(stderr), self.assertRaises(SystemExit):
                module._checkpoint_read_staged(str(target), 1024)
        self.assertIn("changed during verification", stderr.getvalue())
        self.assertEqual(b"substituted\n", target.read_bytes())
        self.assertEqual(b"expected\n", detached.read_bytes())

    def test_restore_interruption_preserves_marker_owned_paths(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module, "_checkpoint_atomic_publish", side_effect=SystemExit(73)
            ):
                with self.assertRaises(SystemExit) as stopped:
                    module.cmd_checkpoint_restore(
                        SimpleNamespace(
                            dir=str(origin),
                            source=str(capsule),
                            manifest_sha256=exported["manifest_sha256"],
                        )
                    )
        self.assertEqual(73, stopped.exception.code)
        marker = origin / ".hexaemeron" / "checkpoint-restore.json"
        self.assertTrue(marker.is_file())
        marker_payload = json.loads(marker.read_bytes())
        stage = Path(marker_payload["stage"])
        self.assertTrue(stage.is_dir())
        retry = self.restore_into(
            origin, capsule, exported["manifest_sha256"], expect=2
        )
        self.assertIn("interrupted before active state", retry.stderr)
        self.assertTrue(stage.is_dir())
        self.assertTrue(marker.is_file())

    def test_restore_interruption_after_publish_finalizes_once(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module, "_checkpoint_restore_internal_checks", side_effect=SystemExit(74)
            ):
                with self.assertRaises(SystemExit):
                    module.cmd_checkpoint_restore(
                        SimpleNamespace(
                            dir=str(origin),
                            source=str(capsule),
                            manifest_sha256=exported["manifest_sha256"],
                        )
                    )
        marker = origin / ".hexaemeron" / "checkpoint-restore.json"
        self.assertTrue(marker.is_file())
        worktree = Path(json.loads(marker.read_bytes())["worktree"])
        ledger_path = worktree / ".hexaemeron" / "ledger.jsonl"
        before = ledger_path.read_bytes()

        result = self.restore_into(origin, capsule, exported["manifest_sha256"])
        self.assertEqual(
            "finalized-interrupted-publication", json.loads(result.stdout)["recovery"]
        )
        self.assertFalse(marker.exists())
        self.assertEqual(before, ledger_path.read_bytes())
        self.assertEqual(
            1,
            sum(
                json.loads(line)["event"] == "checkpoint:restore"
                for line in before.splitlines()
            ),
        )

    def test_restore_interrupted_finalization_rejects_altered_state(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        arguments = SimpleNamespace(
            dir=str(origin),
            source=str(capsule),
            manifest_sha256=exported["manifest_sha256"],
        )
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_internal_checks",
                side_effect=SystemExit(74),
            ):
                with self.assertRaises(SystemExit):
                    module.cmd_checkpoint_restore(arguments)

        marker = origin / ".hexaemeron" / "checkpoint-restore.json"
        worktree = Path(json.loads(marker.read_bytes())["worktree"])
        state_path = worktree / ".hexaemeron" / "state.json"
        ledger_path = worktree / ".hexaemeron" / "ledger.jsonl"
        state = json.loads(state_path.read_bytes())
        state["config"]["audit"]["fold"] = True
        fingerprint = module.state_fingerprint(state)
        lines = ledger_path.read_bytes().splitlines()
        last = json.loads(lines[-1])
        last["state"] = fingerprint
        last["data"]["relocated_state_fingerprint"] = fingerprint
        body = {
            key: last[key] for key in ("ts", "event", "data", "prev", "state")
        }
        last["hash"] = hashlib.sha256(module.canonical(body).encode()).hexdigest()
        state_path.write_bytes(
            json.dumps(state, indent=2, sort_keys=False).encode("utf-8") + b"\n"
        )
        ledger_path.write_bytes(
            b"\n".join(lines[:-1])
            + b"\n"
            + json.dumps(last, sort_keys=True).encode("utf-8")
            + b"\n"
        )

        refused = self.restore_into(
            origin, capsule, exported["manifest_sha256"], expect=2
        )
        self.assertIn("unowned active state", refused.stderr)
        self.assertTrue(marker.is_file())

    def test_restore_interrupted_finalization_rejects_altered_evidence(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        arguments = SimpleNamespace(
            dir=str(origin),
            source=str(capsule),
            manifest_sha256=exported["manifest_sha256"],
        )
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_internal_checks",
                side_effect=SystemExit(74),
            ):
                with self.assertRaises(SystemExit):
                    module.cmd_checkpoint_restore(arguments)

        marker = origin / ".hexaemeron" / "checkpoint-restore.json"
        worktree = Path(json.loads(marker.read_bytes())["worktree"])
        worktree.joinpath(".hexaemeron", ".gitignore").write_text(
            "**\n", encoding="utf-8"
        )

        refused = self.restore_into(
            origin, capsule, exported["manifest_sha256"], expect=2
        )
        self.assertIn("opaque controller evidence", refused.stderr)
        self.assertTrue(marker.is_file())

    def test_restore_active_state_change_during_checks_refuses(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        original_checks = module._checkpoint_restore_internal_checks

        def alter_then_check(worktree, manifest, ledger):
            state_path = Path(worktree) / ".hexaemeron" / "state.json"
            ledger_path = Path(worktree) / ".hexaemeron" / "ledger.jsonl"
            state = json.loads(state_path.read_bytes())
            state["config"]["audit"]["fold"] = True
            fingerprint = module.state_fingerprint(state)
            lines = ledger_path.read_bytes().splitlines()
            last = json.loads(lines[-1])
            last["state"] = fingerprint
            last["data"]["relocated_state_fingerprint"] = fingerprint
            body = {
                key: last[key]
                for key in ("ts", "event", "data", "prev", "state")
            }
            last["hash"] = hashlib.sha256(
                module.canonical(body).encode()
            ).hexdigest()
            state_path.write_bytes(
                json.dumps(state, indent=2, sort_keys=False).encode("utf-8")
                + b"\n"
            )
            ledger_path.write_bytes(
                b"\n".join(lines[:-1])
                + b"\n"
                + json.dumps(last, sort_keys=True).encode("utf-8")
                + b"\n"
            )
            return original_checks(worktree, manifest, ledger)

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_internal_checks",
                side_effect=alter_then_check,
            ):
                with redirect_stdout(StringIO()), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit):
                        module.cmd_checkpoint_restore(
                            SimpleNamespace(
                                dir=str(origin),
                                source=str(capsule),
                                manifest_sha256=exported["manifest_sha256"],
                            )
                        )
        self.assertIn("unowned active state", stderr.getvalue())
        self.assertTrue(
            origin.joinpath(
                ".hexaemeron", "checkpoint-restore.json"
            ).is_file()
        )

    def test_restore_ref_change_during_publication_refuses(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        original_refs = module._checkpoint_refs
        original_publish = module._checkpoint_atomic_publish
        changed = False

        def moving_refs(base_dir, state):
            values = original_refs(base_dir, state)
            if changed:
                values[next(iter(values))] = "9" * 40
            return values

        def move_ref_then_publish(stage, destination):
            nonlocal changed
            changed = True
            return original_publish(stage, destination)

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(module, "_checkpoint_refs", moving_refs):
                with mock.patch.object(
                    module, "_checkpoint_atomic_publish", move_ref_then_publish
                ):
                    with redirect_stderr(stderr), self.assertRaises(SystemExit):
                        module.cmd_checkpoint_restore(
                            SimpleNamespace(
                                dir=str(origin),
                                source=str(capsule),
                                manifest_sha256=exported["manifest_sha256"],
                            )
                        )
        self.assertIn("refs changed during publication", stderr.getvalue())
        self.assertTrue(
            origin.joinpath(
                ".hexaemeron", "checkpoint-restore.json"
            ).is_file()
        )

    def test_restore_worktree_branch_change_during_checks_refuses(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        original_checks = module._checkpoint_restore_internal_checks
        real_git = shutil.which("git")

        def detach_after_checks(worktree, manifest, ledger):
            result = original_checks(worktree, manifest, ledger)
            subprocess.run(
                [real_git, "-C", worktree, "checkout", "--detach", "main"],
                check=True,
                capture_output=True,
            )
            return result

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_internal_checks",
                side_effect=detach_after_checks,
            ):
                with redirect_stdout(StringIO()), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit):
                        module.cmd_checkpoint_restore(
                            SimpleNamespace(
                                dir=str(origin),
                                source=str(capsule),
                                manifest_sha256=exported["manifest_sha256"],
                            )
                        )
        self.assertIn("worktree branch changed", stderr.getvalue())
        self.assertTrue(
            origin.joinpath(
                ".hexaemeron", "checkpoint-restore.json"
            ).is_file()
        )

    def test_restore_moved_worktree_during_checks_refuses(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        original_checks = module._checkpoint_restore_internal_checks
        detached = None

        def move_after_checks(worktree, manifest, ledger):
            nonlocal detached
            result = original_checks(worktree, manifest, ledger)
            worktree_path = Path(worktree)
            detached = worktree_path.with_name(worktree_path.name + "-detached")
            worktree_path.rename(detached)
            worktree_path.symlink_to(detached, target_is_directory=True)
            return result

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_internal_checks",
                side_effect=move_after_checks,
            ):
                with redirect_stdout(StringIO()), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit):
                        module.cmd_checkpoint_restore(
                            SimpleNamespace(
                                dir=str(origin),
                                source=str(capsule),
                                manifest_sha256=exported["manifest_sha256"],
                            )
                        )
        self.assertTrue(detached.is_dir())
        self.assertTrue(
            origin.joinpath(
                ".hexaemeron", "checkpoint-restore.json"
            ).is_file()
        )

    def test_restore_replaced_marker_is_not_deleted(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        arguments = SimpleNamespace(
            dir=str(origin),
            source=str(capsule),
            manifest_sha256=exported["manifest_sha256"],
        )
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_internal_checks",
                side_effect=SystemExit(74),
            ):
                with self.assertRaises(SystemExit):
                    module.cmd_checkpoint_restore(arguments)

        marker = origin / ".hexaemeron" / "checkpoint-restore.json"
        original_checks = module._checkpoint_restore_internal_checks

        def replace_marker(*args):
            result = original_checks(*args)
            replacement = marker.with_suffix(".replacement")
            replacement.write_text("unowned replacement\n", encoding="utf-8")
            os.replace(replacement, marker)
            return result

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_internal_checks",
                side_effect=replace_marker,
            ):
                with redirect_stderr(stderr), self.assertRaises(SystemExit):
                    module.cmd_checkpoint_restore(arguments)
        self.assertIn("marker changed before retirement", stderr.getvalue())
        self.assertEqual("unowned replacement\n", marker.read_text(encoding="utf-8"))

    def test_restore_hostile_breadcrumb_is_not_followed(self):
        self.to_post_push()
        capsule, _, exported = self.export("capsule")
        origin, _ = self.fresh_origin_for(capsule)
        module = hexctl_module()
        outside = Path(self.dir) / "outside-breadcrumb"
        outside.write_text("unowned breadcrumb target\n", encoding="utf-8")
        original_checks = module._checkpoint_restore_internal_checks

        def inject_breadcrumb(*args):
            result = original_checks(*args)
            os.symlink(
                outside,
                origin.joinpath(".hexaemeron", module.WORKTREE_FILE),
            )
            return result

        stderr = StringIO()
        with mock.patch.dict(os.environ, self.direct_environment(), clear=True):
            with mock.patch.object(
                module,
                "_checkpoint_restore_internal_checks",
                side_effect=inject_breadcrumb,
            ):
                with redirect_stdout(StringIO()), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit):
                        module.cmd_checkpoint_restore(
                            SimpleNamespace(
                                dir=str(origin),
                                source=str(capsule),
                                manifest_sha256=exported["manifest_sha256"],
                            )
                        )
        self.assertIn("breadcrumb", stderr.getvalue())
        self.assertEqual(
            "unowned breadcrumb target\n", outside.read_text(encoding="utf-8")
        )
        self.assertTrue(
            origin.joinpath(".hexaemeron", module.WORKTREE_FILE).is_symlink()
        )
        self.assertTrue(
            origin.joinpath(
                ".hexaemeron", "checkpoint-restore.json"
            ).is_file()
        )


if __name__ == "__main__":
    unittest.main()
