"""Issue 891: Fiat sync receipts must expose whole-side and rebuild loss."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEXCTL = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"


def controller_module():
    spec = importlib.util.spec_from_file_location(
        "hexctl_sync_resolution_guard_under_test", HEXCTL
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(directory: str, *args: str) -> str:
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("GIT_")
    }
    result = subprocess.run(
        [
            "git",
            "-C",
            directory,
            "-c",
            "commit.gpgsign=false",
            "-c",
            "tag.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return result.stdout.strip()


def write(directory: str, relative: str, content: str) -> None:
    target = Path(directory, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def commit_all(directory: str, message: str) -> str:
    git(directory, "add", "-A")
    git(directory, "commit", "--quiet", "--no-gpg-sign", "-m", message)
    return git(directory, "rev-parse", "HEAD")


def merge_commit(directory: str, tree: str, left: str, right: str, message: str) -> str:
    return git(
        directory,
        "commit-tree",
        tree,
        "-p",
        left,
        "-p",
        right,
        "-m",
        message,
    )


class SyncResolutionGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = self.temporary.name
        git(self.directory, "init", "--quiet", "-b", "main")
        git(self.directory, "config", "user.name", "Fixture")
        git(self.directory, "config", "user.email", "fixture@example.invalid")
        write(self.directory, "registry.json", '{"base":0,"product":0}\n')
        self.anchor = commit_all(self.directory, "anchor")

        git(self.directory, "checkout", "--quiet", "-b", "product", self.anchor)
        write(self.directory, "registry.json", '{"base":0,"product":1}\n')
        self.product = commit_all(self.directory, "product")

        git(self.directory, "checkout", "--quiet", "-b", "base", self.anchor)
        write(self.directory, "registry.json", '{"base":1,"product":0}\n')
        self.base = commit_all(self.directory, "base")
        self.module = controller_module()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def tree_with_registry(self, content: str) -> str:
        git(self.directory, "checkout", "--quiet", "--detach", self.product)
        write(self.directory, "registry.json", content)
        git(self.directory, "add", "registry.json")
        tree = git(self.directory, "write-tree")
        git(self.directory, "reset", "--quiet", "--hard", self.product)
        return tree

    def guard(self, sync: str, *, current_sync=None, acknowledgements=()):
        return self.module.sync_resolution_guard_record(
            self.directory,
            self.product,
            self.base,
            sync,
            current_sync=current_sync,
            acknowledgements=list(acknowledgements),
        )

    def test_first_sync_refuses_a_whole_side_until_the_exact_path_is_acknowledged(self):
        product_tree = git(self.directory, "rev-parse", f"{self.product}^{{tree}}")
        sync = merge_commit(
            self.directory, product_tree, self.product, self.base, "whole product side"
        )

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.guard(sync)
        self.assertIn("--acknowledge-sync-path", stderr.getvalue())
        self.assertIn("registry.json", stderr.getvalue())

        record = self.guard(sync, acknowledgements=("registry.json",))
        self.assertEqual(record["side_selected_paths"], ["registry.json"])
        self.assertEqual(record["superseded_intersection_paths"], [])
        self.assertEqual(record["acknowledged_paths"], ["registry.json"])

    def test_first_sync_accepts_a_semantic_union_without_acknowledgement(self):
        union_tree = self.tree_with_registry('{"base":1,"product":1}\n')
        sync = merge_commit(
            self.directory, union_tree, self.product, self.base, "semantic union"
        )

        record = self.guard(sync)

        self.assertEqual(record["side_selected_paths"], [])
        self.assertEqual(record["superseded_intersection_paths"], [])
        self.assertEqual(record["acknowledged_paths"], [])

    def test_rebuilt_sync_requires_the_old_composition_base_advance_intersection(self):
        union_tree = self.tree_with_registry('{"base":1,"product":1}\n')
        old_sync = merge_commit(
            self.directory, union_tree, self.product, self.base, "old semantic union"
        )
        git(self.directory, "checkout", "--quiet", "base")
        write(self.directory, "registry.json", '{"base":2,"product":0}\n')
        new_base = commit_all(self.directory, "base advances registry")
        rebuilt_tree = self.tree_with_registry('{"base":2,"product":1}\n')
        rebuilt = merge_commit(
            self.directory, rebuilt_tree, self.product, new_base, "rebuilt semantic union"
        )
        self.base = new_base
        current_sync = {"commit": old_sync, "base_head": self.base_parent(new_base)}

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.guard(rebuilt, current_sync=current_sync)
        self.assertIn("registry.json", stderr.getvalue())

        record = self.guard(
            rebuilt,
            current_sync=current_sync,
            acknowledgements=("registry.json",),
        )
        self.assertEqual(record["side_selected_paths"], [])
        self.assertEqual(
            record["superseded_intersection_paths"], ["registry.json"]
        )
        self.assertEqual(record["acknowledged_paths"], ["registry.json"])

    def base_parent(self, commit: str) -> str:
        return git(self.directory, "rev-parse", f"{commit}^")

    def test_acknowledgements_are_an_exact_sorted_unique_set(self):
        write(self.directory, "z-registry.json", "anchor\n")
        anchor = commit_all(self.directory, "second registry anchor")
        git(self.directory, "checkout", "--quiet", "-B", "product-two", anchor)
        write(self.directory, "registry.json", "product\n")
        write(self.directory, "z-registry.json", "product\n")
        product = commit_all(self.directory, "two product registries")
        git(self.directory, "checkout", "--quiet", "-B", "base-two", anchor)
        write(self.directory, "registry.json", "base\n")
        write(self.directory, "z-registry.json", "base\n")
        base = commit_all(self.directory, "two base registries")
        product_tree = git(self.directory, "rev-parse", f"{product}^{{tree}}")
        sync = merge_commit(self.directory, product_tree, product, base, "take product")

        for acknowledgements in (
            ["z-registry.json", "registry.json"],
            ["registry.json", "registry.json", "z-registry.json"],
            ["registry.json"],
            ["registry.json", "not-risky.json", "z-registry.json"],
        ):
            with self.subTest(acknowledgements=acknowledgements):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                    SystemExit
                ):
                    self.module.sync_resolution_guard_record(
                        self.directory,
                        product,
                        base,
                        sync,
                        current_sync=None,
                        acknowledgements=acknowledgements,
                    )

        record = self.module.sync_resolution_guard_record(
            self.directory,
            product,
            base,
            sync,
            current_sync=None,
            acknowledgements=["registry.json", "z-registry.json"],
        )
        self.assertEqual(
            record["acknowledged_paths"], ["registry.json", "z-registry.json"]
        )

    def test_parser_preserves_repeated_path_acknowledgements(self):
        args = self.module.build_parser().parse_args(
            [
                "--dir",
                self.directory,
                "done",
                "sync-run",
                "--acknowledge-sync-path",
                "a.json",
                "--acknowledge-sync-path",
                "b.json",
            ]
        )
        self.assertEqual(args.acknowledge_sync_paths, ["a.json", "b.json"])

    def test_stored_guard_replays_and_tampering_refuses(self):
        union_tree = self.tree_with_registry('{"base":1,"product":1}\n')
        sync_commit = merge_commit(
            self.directory, union_tree, self.product, self.base, "semantic union"
        )
        guard = self.guard(sync_commit)
        sync = {
            "commit": sync_commit,
            "base_head": self.base,
            "resolution_guard": guard,
        }

        self.assertEqual(
            self.module._require_sync_resolution_guard(
                self.directory,
                sync,
                self.product,
                previous_sync=None,
            ),
            guard,
        )

        sync["resolution_guard"] = dict(guard)
        sync["resolution_guard"]["side_selected_paths"] = ["registry.json"]
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.module._require_sync_resolution_guard(
                self.directory,
                sync,
                self.product,
                previous_sync=None,
            )

    def test_legacy_active_sync_names_fresh_supersession_as_recovery(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.module._require_sync_resolution_guard(
                self.directory,
                {"commit": self.product, "base_head": self.base},
                self.product,
                previous_sync=None,
            )
        self.assertIn("fresh signed and revalidated sync", stderr.getvalue())

    def test_malformed_tree_output_refuses_without_a_traceback(self):
        stderr = io.StringIO()
        with (
            mock.patch.object(
                self.module,
                "_native_relation_git",
                return_value=b"not-an-ls-tree-record\0",
            ),
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit),
        ):
            self.module._sync_tree_entries(
                self.directory,
                self.product,
                ["registry.json"],
                "sync resolution specimen",
            )
        self.assertIn("malformed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_tree_reader_treats_pathspec_magic_as_literal(self):
        write(self.directory, "registry[1].json", "literal\n")
        commit = commit_all(self.directory, "literal pathspec specimen")

        entries = self.module._sync_tree_entries(
            self.directory,
            commit,
            ["registry[1].json"],
            "sync resolution literal specimen",
        )

        self.assertEqual(list(entries), ["registry[1].json"])
        self.assertIsNotNone(entries["registry[1].json"])


if __name__ == "__main__":
    unittest.main()
