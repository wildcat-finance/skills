"""Issue 774: integration revalidation is bounded apart from the other readers.

`GIT_PATHS_MAX` served five call sites. Two of them read a surface that grows
with the base every time somebody else merges; three do not. The shared
constant therefore refused completed runs that had nothing wrong with them,
which is where issue 556 stopped.

These cases pin both halves. The guard cases fail with `INTEGRATION_PATHS_MAX`
reverted to `GIT_PATHS_MAX`. The pin cases pass either way by design: they
exist so a later reader cannot mistake one of the three unchanged sites for a
sixth integration surface.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEXCTL = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"

AGGREGATE_ID = "promise-machine-portable-runtime-v1"
AGGREGATE_PREFIX = ".agents/skills/promise-machine/runtime/"

# Issue 556 measured 702 paths that no registered generator owns. Anything over
# 500 reproduces its refusal; 600 keeps the fixture repository cheap to build.
OUTSIDE_FILE_COUNT = 600

# The count #679's regression fixture used, recovered from merge cb502e55.
V1_PATH_COUNT = 907


def controller_module():
    spec = importlib.util.spec_from_file_location(
        "hexctl_integration_path_bounds_under_test", HEXCTL
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(directory, *args, **kwargs):
    return subprocess.run(
        ["git", "-C", str(directory), *args],
        check=True,
        capture_output=True,
        text=True,
        **kwargs,
    ).stdout.strip()


def init_repository(directory):
    """A repository that signs nothing and depends on no ambient config."""
    git(directory, "init", "--quiet", "-b", "main")
    for key, value in (
        ("user.name", "Fixture"),
        ("user.email", "fixture@example.invalid"),
        ("commit.gpgsign", "false"),
        ("tag.gpgsign", "false"),
        ("gc.auto", "0"),
    ):
        git(directory, "config", key, value)


def write_file(directory, relative, content):
    path = Path(directory) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def commit_all(directory, message):
    git(directory, "add", "-A")
    git(directory, "commit", "--quiet", "--no-gpg-sign", "-m", message)
    return git(directory, "rev-parse", "HEAD")


def build_runtime_aggregate(directory):
    """A real registered aggregate: payload blobs and a manifest over them.

    The registry pins the prefix, generator, schema, contract and manifest
    name, so the aggregate can be built here rather than borrowed from a
    fixture that names a commit no fresh clone can reach.
    """
    payload = {
        "promise_machine.py": "# portable runtime payload\n",
        "contracts/example.json": '{"contract": "promise-machine/v1"}\n',
    }
    rows = []
    for relative, content in sorted(payload.items()):
        encoded = content.encode("utf-8")
        write_file(directory, AGGREGATE_PREFIX + relative, content)
        rows.append(
            {
                "bytes": len(encoded),
                "path": relative,
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "source": "scripts/portable_promise_machine.py",
            }
        )
    manifest = {
        "schema": "promise-machine-portable-runtime/v1",
        "contract": "promise-machine/v1",
        "generated_by": "scripts/portable_promise_machine.py",
        # The manifest counts payload rows; the declaration counts the manifest too.
        "file_count": len(rows),
        "total_bytes": sum(row["bytes"] for row in rows),
        "omissions": [],
        "files": rows,
    }
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    write_file(
        directory,
        AGGREGATE_PREFIX + "MANIFEST.json",
        manifest_bytes.decode("utf-8"),
    )
    return {
        "id": AGGREGATE_ID,
        "prefix": AGGREGATE_PREFIX,
        "generator": "scripts/portable_promise_machine.py",
        "manifest": "MANIFEST.json",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "file_count": len(rows) + 1,
    }


def aggregate_tree_digest(module, directory, commit):
    """The declaration's tree digest, read back through the controller.

    The reading is the controller's own; only the digest composition is
    mirrored, which is what a declaration has to supply from outside. Issue 710
    owns the composition itself.
    """
    registry = module.GENERATOR_AGGREGATE_REGISTRY[AGGREGATE_ID]
    _, rows = module._git_aggregate_tree(directory, commit, AGGREGATE_ID, registry)
    blobs = module._git_batch_blobs(
        directory, AGGREGATE_ID, rows, registry["max_bytes"]
    )
    digests = []
    for row in rows:
        data = blobs[row["path"]]
        digests.append(
            (
                row["path"],
                hashlib.sha256(
                    module.GENERATOR_AGGREGATE_FILE_DIGEST_DOMAIN
                    + row["path"].encode("utf-8")
                    + b"\0"
                    + row["mode"].encode("ascii")
                    + b"\0"
                    + str(len(data)).encode("ascii")
                    + b"\0"
                    + hashlib.sha256(data).hexdigest().encode("ascii")
                ).digest(),
            )
        )
    digests.sort(key=lambda item: item[0])
    return hashlib.sha256(
        module.GENERATOR_AGGREGATE_TREE_DIGEST_DOMAIN
        + b"".join(digest for _, digest in digests)
    ).hexdigest()


class IntegrationBoundTests(unittest.TestCase):
    """The bound itself, at the two sites that read an integration surface."""

    @classmethod
    def setUpClass(cls):
        cls.module = controller_module()

    def refusal(self, callable_object, *args, **kwargs):
        error = StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as stopped:
            callable_object(*args, **kwargs)
        self.assertEqual(stopped.exception.code, 2)
        return error.getvalue()

    def diff_bytes(self, paths):
        return b"\0".join(path.encode("utf-8") for path in paths) + b"\0"

    def test_the_integration_bound_is_distinct_from_the_shared_one(self):
        self.assertEqual(self.module.GIT_PATHS_MAX, 500)
        self.assertEqual(self.module.INTEGRATION_PATHS_MAX, 4096)
        self.assertGreater(
            self.module.INTEGRATION_PATHS_MAX, self.module.GIT_PATHS_MAX
        )

    def test_git_diff_paths_accepts_the_ceiling_and_refuses_one_over(self):
        limit = self.module.INTEGRATION_PATHS_MAX
        at_limit = [f"runtime/file-{number:05d}.py" for number in range(limit)]
        over_limit = at_limit + [f"runtime/file-{limit:05d}.py"]

        with mock.patch.object(
            self.module, "bounded_git", return_value=self.diff_bytes(at_limit)
        ):
            accepted = self.module.git_diff_paths(str(ROOT), "a" * 40, "b" * 40)
        self.assertEqual(len(accepted), limit)

        with mock.patch.object(
            self.module, "bounded_git", return_value=self.diff_bytes(over_limit)
        ):
            message = self.refusal(
                self.module.git_diff_paths, str(ROOT), "a" * 40, "b" * 40
            )
        self.assertIn(f"exceeds {limit} paths", message)
        self.assertNotIn("exceeds 500 paths", message)

    def test_manifest_paths_accepts_the_ceiling_and_refuses_one_over(self):
        limit = self.module.INTEGRATION_PATHS_MAX
        at_limit = sorted(f"runtime/file-{number:05d}.py" for number in range(limit))
        over_limit = sorted(at_limit + [f"runtime/file-{limit:05d}.py"])

        self.assertEqual(
            len(self.module._manifest_paths(at_limit, "affected_paths")), limit
        )

        message = self.refusal(
            self.module._manifest_paths, over_limit, "affected_paths"
        )
        self.assertIn(f"at most {limit} paths", message)
        self.assertNotIn("at most 500 paths", message)


class UnchangedBoundTests(unittest.TestCase):
    """The three sites that keep 500, pinned so nobody widens them by accident."""

    @classmethod
    def setUpClass(cls):
        cls.module = controller_module()

    def refusal(self, callable_object, *args, **kwargs):
        error = StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as stopped:
            callable_object(*args, **kwargs)
        self.assertEqual(stopped.exception.code, 2)
        return error.getvalue()

    def test_the_commit_range_still_refuses_over_500_commits(self):
        limit = self.module.GIT_PATHS_MAX
        commits = "\n".join(f"{number:040x}" for number in range(limit + 1))

        def fake_bounded_git(base_dir, argv, message=None, **kwargs):
            if argv[0] == "rev-list":
                return commits.encode("ascii")
            return b""

        with mock.patch.object(
            self.module, "resolved_commit", side_effect=lambda *a, **k: "c" * 40
        ), mock.patch.object(
            self.module, "bounded_git", side_effect=fake_bounded_git
        ):
            message = self.refusal(
                self.module.exact_commit_range,
                str(ROOT),
                "base",
                "head",
                "step range",
            )
        self.assertIn(f"commit range exceeds {limit} commits", message)
        self.assertNotIn("4096", message)

    def test_the_prose_diff_reader_still_refuses_over_500_paths(self):
        limit = self.module.GIT_PATHS_MAX
        paths = [f"docs/file-{number:05d}.md" for number in range(limit + 1)]
        raw = b"\0".join(path.encode("utf-8") for path in paths) + b"\0"

        with mock.patch.object(self.module, "bounded_git", return_value=raw):
            message = self.refusal(
                self.module.scribe_files, str(ROOT), "base-branch", "head-branch"
            )
        self.assertIn(f"more than {limit} paths", message)
        self.assertNotIn("4096", message)

    def test_the_checkpoint_ref_set_still_refuses_over_500_refs(self):
        limit = self.module.GIT_PATHS_MAX
        state = {
            "base": "main",
            "run_branch": "fiat/example",
            "config": {"git": {"base": "main"}},
            "steps": [
                {
                    "receipts": {
                        "implement": {"branch": f"fiat/example-step-{number}"}
                    }
                }
                for number in range(limit + 1)
            ],
        }
        message = self.refusal(self.module._checkpoint_ref_names, state)
        self.assertIn("ref set is duplicated or too large", message)


class IntegrationSurfaceTests(unittest.TestCase):
    """Whole revalidation records, over the surfaces that used to refuse."""

    @classmethod
    def setUpClass(cls):
        cls.module = controller_module()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.realpath(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def write_artifact(self, document, name="revalidation.json"):
        if isinstance(document, (bytes, bytearray)):
            payload = bytes(document)
        else:
            payload = json.dumps(document).encode("utf-8")
        (Path(self.dir) / name).write_bytes(payload)
        return name

    def refusal(self, *args, **kwargs):
        error = StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as stopped:
            self.module.integration_revalidation_record(*args, **kwargs)
        self.assertEqual(stopped.exception.code, 2)
        return error.getvalue()

    def v1_record_over(self, paths):
        """Drive the version-1 route with a synthesised path delta."""
        artifact = self.write_artifact(
            {
                "schema": "fiat-integration-revalidation/v1",
                "affected_paths": paths,
                "checks": [
                    {
                        "id": "portable-runtime-suite",
                        "command": "python3 -m unittest discover -s tests",
                        "paths": paths,
                        "exit": 0,
                    }
                ],
            }
        )
        product_head, base_head, sync_head = ("1" * 40, "2" * 40, "3" * 40)
        deltas = {
            ("0" * 40, product_head): ["product.py"],
            ("0" * 40, base_head): list(paths),
            (product_head, sync_head): list(paths),
        }
        with mock.patch.object(
            self.module, "merge_base_commit", return_value="0" * 40
        ), mock.patch.object(
            self.module,
            "git_diff_paths",
            side_effect=lambda base_dir, before, after: sorted(
                deltas[(before, after)]
            ),
        ):
            return self.module.integration_revalidation_record(
                self.dir, artifact, product_head, base_head, sync_head
            )

    def test_a_v1_surface_of_907_individual_paths_is_accepted(self):
        paths = sorted(
            f"{AGGREGATE_PREFIX}plugins/example/file-{number:04d}.md"
            for number in range(V1_PATH_COUNT)
        )
        record = self.v1_record_over(paths)
        self.assertEqual(record["schema"], "fiat-integration-revalidation/v1")
        self.assertEqual(len(record["affected_paths"]), V1_PATH_COUNT)
        self.assertEqual(len(record["composition_paths"]), V1_PATH_COUNT)

    def test_a_small_v1_surface_under_500_paths_is_unchanged(self):
        paths = sorted(f"docs/file-{number:03d}.md" for number in range(12))
        record = self.v1_record_over(paths)
        self.assertEqual(record["affected_paths"], paths)
        self.assertEqual(record["checks"][0]["paths"], paths)
        self.assertEqual(record["base_after"], "2" * 40)

    def test_an_oversized_artifact_refuses_whatever_its_path_count(self):
        filler = "x" * (self.module.SOURCE_BYTES_MAX + 1)
        artifact = self.write_artifact(
            json.dumps(
                {
                    "schema": "fiat-integration-revalidation/v1",
                    "affected_paths": ["docs/one.md"],
                    "checks": [
                        {
                            "id": "padding",
                            "command": filler,
                            "paths": ["docs/one.md"],
                            "exit": 0,
                        }
                    ],
                }
            ).encode("utf-8")
        )
        message = self.refusal(
            self.dir, artifact, "1" * 40, "2" * 40, "3" * 40
        )
        self.assertIn(f"{self.module.SOURCE_BYTES_MAX}-byte cap", message)


class V2OutsideSurfaceTests(unittest.TestCase):
    """The route issue 556 needs: a real aggregate and 600 outside paths.

    The repository is built here rather than borrowed from the issue 710
    fixture, whose sync commit is unreachable in a fresh clone.
    """

    @classmethod
    def setUpClass(cls):
        cls.module = controller_module()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = os.path.realpath(cls.tmp.name)
        init_repository(cls.dir)

        write_file(cls.dir, "README.md", "# fixture\n")
        cls.merge_base = commit_all(cls.dir, "base")

        write_file(cls.dir, "product.py", "# product\n")
        cls.product_head = commit_all(cls.dir, "product")

        git(cls.dir, "checkout", "--quiet", "-b", "upstream", cls.merge_base)
        for number in range(OUTSIDE_FILE_COUNT):
            write_file(
                cls.dir,
                f"plugins/example/source-{number:04d}.md",
                f"# outside {number}\n",
            )
        cls.base_head = commit_all(cls.dir, "upstream breadth")

        git(cls.dir, "checkout", "--quiet", "main")
        git(cls.dir, "merge", "--quiet", "--no-ff", "--no-gpg-sign",
            "-m", "sync", "upstream")
        cls.declaration = build_runtime_aggregate(cls.dir)
        cls.sync_head = commit_all(cls.dir, "sync with generated runtime")
        cls.declaration["tree_sha256"] = aggregate_tree_digest(
            cls.module, cls.dir, cls.sync_head
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def outside_paths(self):
        return sorted(
            f"plugins/example/source-{number:04d}.md"
            for number in range(OUTSIDE_FILE_COUNT)
        )

    def test_a_v2_artifact_with_more_than_500_outside_paths_is_accepted(self):
        outside = self.outside_paths()
        self.assertGreater(len(outside), self.module.GIT_PATHS_MAX)

        artifact = {
            "schema": "fiat-integration-revalidation/v2",
            "affected_paths": outside,
            "affected_aggregates": [dict(self.declaration)],
            "checks": [
                {
                    "id": "portable-runtime",
                    "command": "python3 scripts/portable_promise_machine.py check",
                    "paths": [],
                    "aggregates": [AGGREGATE_ID],
                    "exit": 0,
                },
                {
                    "id": "outside-surface",
                    "command": "python3 plugins/hexaemeron/tests/run_tests.py",
                    "paths": outside,
                    "aggregates": [],
                    "exit": 0,
                },
            ],
        }
        name = "revalidation-v2.json"
        (Path(self.dir) / name).write_text(
            json.dumps(artifact), encoding="utf-8"
        )

        record = self.module.integration_revalidation_record(
            self.dir, name, self.product_head, self.base_head, self.sync_head
        )

        self.assertEqual(record["schema"], "fiat-integration-revalidation/v2")
        self.assertEqual(record["individual_path_count"], OUTSIDE_FILE_COUNT)
        self.assertEqual(
            record["aggregate_owned_path_count"],
            self.declaration["file_count"],
        )
        self.assertEqual(record["affected_paths"], outside)


if __name__ == "__main__":
    unittest.main()
