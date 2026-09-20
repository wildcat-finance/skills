"""A portable copy keeps one complete, unchanged Lazarus release fixture."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("plugins/lazarus/examples/aave-v4-spoke-v1")
RETAINED = Path("plugins/lazarus/examples/aave-v4-spoke-v1-release/fixture")
PAYLOADS = (
    "anchors.jsonl", "header.json", "plan.json", "proofs.jsonl",
    "receipt-witness.json", "rpc.jsonl",
)


def generator():
    spec = importlib.util.spec_from_file_location(
        "portable_duplicate_fixture", ROOT / "scripts/portable_promise_machine.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortableDuplicateFixtureTests(unittest.TestCase):
    def setUp(self):
        self.module = generator()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.tracked = []
        for prefix in (SOURCE, RETAINED):
            for name in PAYLOADS:
                relative = prefix / name
                path = self.root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((name + "\n").encode())
                path.chmod(0o644)
                self.tracked.append(relative)

    def check_pair(self):
        check = getattr(self.module, "check_duplicate_fixture_payload", None)
        self.assertTrue(callable(check), "omission must verify its retained copy")
        return check(self.root, self.tracked)

    def test_duplicate_payload_is_not_copied_twice(self):
        for name in PAYLOADS:
            with self.subTest(name=name):
                self.assertTrue(self.module._omitted(SOURCE / name))
                self.assertFalse(self.module._omitted(RETAINED / name))

    def test_manifest_program_and_other_examples_stay_present(self):
        for relative in (
            SOURCE / "manifest.json", SOURCE / "demo.py", SOURCE / "new.json",
            SOURCE / "nested/rpc.jsonl",
            Path("plugins/lazarus/examples/aave-v4-spoke-v0/rpc.jsonl"),
        ):
            with self.subTest(path=relative):
                self.assertFalse(self.module._omitted(relative))

    def test_identical_regular_copies_are_admitted(self):
        self.check_pair()

    def test_changed_copy_is_refused(self):
        (self.root / RETAINED / "rpc.jsonl").write_bytes(b"different\n")
        with self.assertRaisesRegex(self.module.PackageError, "duplicate fixture"):
            self.check_pair()

    def test_missing_or_untracked_copy_is_refused(self):
        self.tracked.remove(RETAINED / "rpc.jsonl")
        with self.assertRaisesRegex(self.module.PackageError, "duplicate fixture"):
            self.check_pair()

    def test_missing_tracked_copy_is_refused(self):
        (self.root / RETAINED / "rpc.jsonl").unlink()
        with self.assertRaisesRegex(self.module.PackageError, "duplicate fixture"):
            self.check_pair()

    def test_source_selection_checks_pair_before_omission(self):
        check = getattr(self.module, "check_duplicate_fixture_payload", None)
        self.assertTrue(callable(check), "source selection needs the duplicate guard")
        with mock.patch.object(self.module, "_tracked_plugin_files", return_value=self.tracked):
            with mock.patch.object(
                self.module, "check_duplicate_fixture_payload",
                side_effect=self.module.PackageError("duplicate fixture guard refused"),
            ):
                with self.assertRaisesRegex(self.module.PackageError, "duplicate fixture"):
                    self.module._source_candidates(self.root)

    def test_symlinked_component_is_refused(self):
        path = self.root / RETAINED / "rpc.jsonl"
        path.unlink()
        path.symlink_to(self.root / SOURCE / "rpc.jsonl")
        with self.assertRaisesRegex(self.module.PackageError, "duplicate fixture"):
            self.check_pair()

    def test_symlinked_parent_is_refused(self):
        original = self.root / RETAINED
        moved = original.with_name("held-fixture")
        original.rename(moved)
        original.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(self.module.PackageError, "duplicate fixture"):
            self.check_pair()

    def test_changed_mode_is_refused(self):
        (self.root / RETAINED / "rpc.jsonl").chmod(0o755)
        with self.assertRaisesRegex(self.module.PackageError, "duplicate fixture"):
            self.check_pair()


if __name__ == "__main__":
    unittest.main()
