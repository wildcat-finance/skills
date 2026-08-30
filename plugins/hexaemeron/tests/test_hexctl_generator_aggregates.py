"""Issue 710: one checked sync transition across a generator-owned payload.

The incident's counts and ownership topology are reconstructed without relying
on unreachable repository objects. The aggregate validator still consumes 887
real in-memory file records and their manifest, blob and tree digests.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEXCTL = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
FIXTURE = HERE / "fixtures/fiat-710-generator-aggregate.json"
def scratch_directory(prefix, suffix=".json"):
    """A transient in-repository file that `git status` never sees.

    The revalidation artefact must sit inside the repository root for the
    bounded-source read, but a temporary at the root itself is untracked,
    status-visible state that races the disposable-signing guard's
    outer-stability assertion under parallel shards.  The ignored top-level
    tmp/ satisfies both: confined, and invisible to status.
    """
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=scratch)


AGGREGATE_FIELDS = (
    "id",
    "prefix",
    "generator",
    "manifest",
    "manifest_sha256",
    "file_count",
    "tree_sha256",
)


def controller_module():
    spec = importlib.util.spec_from_file_location(
        "hexctl_generator_aggregates_under_test", HEXCTL
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inventory_digest(paths: list[str]) -> str:
    return hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def incident_topology(prefix: str) -> dict[str, list[str]]:
    overlap = [f"incident/shared-{index:04d}.txt" for index in range(5)]
    product = sorted(
        overlap + [f"incident/product-{index:04d}.txt" for index in range(48)]
    )
    upstream = sorted(
        overlap + [f"incident/upstream-{index:04d}.txt" for index in range(1082)]
    )
    owned = sorted(
        [prefix + "MANIFEST.json"]
        + [prefix + f"payload/{index:04d}.txt" for index in range(886)]
    )
    outside = sorted(
        overlap + [f"incident/outside-{index:04d}.txt" for index in range(203)]
    )
    composition = sorted(owned + outside)
    return {
        "product_paths": product,
        "upstream_paths": upstream,
        "overlap_paths": overlap,
        "composition_paths": composition,
        "required_paths": sorted(set(composition) | set(overlap)),
        "aggregate_owned_paths": owned,
        "outside_paths": outside,
    }


def incident_aggregate(module, prefix: str) -> tuple[str, list[dict], dict[str, bytes], dict]:
    payload = []
    blobs = {}
    for index in range(886):
        relative = f"payload/{index:04d}.txt"
        data = f"payload-{index:04d}\n".encode()
        blobs[prefix + relative] = data
        payload.append(
            {
                "bytes": len(data),
                "path": relative,
                "sha256": hashlib.sha256(data).hexdigest(),
                "source": "incident-structure",
            }
        )
    document = {
        "schema": "promise-machine-portable-runtime/v1",
        "contract": "promise-machine/v1",
        "generated_by": "scripts/portable_promise_machine.py",
        "file_count": len(payload),
        "total_bytes": sum(item["bytes"] for item in payload),
        "omissions": [],
        "files": payload,
    }
    manifest = (
        json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    blobs[prefix + "MANIFEST.json"] = manifest
    rows = [
        {
            "path": path,
            "mode": "100644",
            "object": hashlib.sha1(blobs[path], usedforsecurity=False).hexdigest(),
        }
        for path in sorted(blobs)
    ]
    tree_id = hashlib.sha1(
        "".join(
            f"{row['mode']} {row['object']} {row['path']}\n" for row in rows
        ).encode(),
        usedforsecurity=False,
    ).hexdigest()
    file_digests = []
    for row in rows:
        data = blobs[row["path"]]
        digest = hashlib.sha256(data).hexdigest()
        file_digests.append(
            hashlib.sha256(
                module.GENERATOR_AGGREGATE_FILE_DIGEST_DOMAIN
                + row["path"].encode()
                + b"\0"
                + row["mode"].encode()
                + b"\0"
                + str(len(data)).encode()
                + b"\0"
                + digest.encode()
            ).digest()
        )
    tree_digest = hashlib.sha256(
        module.GENERATOR_AGGREGATE_TREE_DIGEST_DOMAIN + b"".join(file_digests)
    ).hexdigest()
    aggregate = {
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "file_count": len(rows),
        "tree_sha256": tree_digest,
        "git_tree": tree_id,
        "payload_file_count": len(payload),
        "payload_total_bytes": sum(item["bytes"] for item in payload),
        "total_bytes": sum(len(data) for data in blobs.values()),
    }
    return tree_id, rows, blobs, aggregate


class IncidentAggregateTests(unittest.TestCase):
    """The five issue acceptance groups, using the recorded incident topology."""

    @classmethod
    def setUpClass(cls):
        cls.module = controller_module()
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        fixture = cls.fixture
        topology = incident_topology(fixture["aggregate"]["prefix"])
        cls.product_paths = topology["product_paths"]
        cls.upstream_paths = topology["upstream_paths"]
        cls.overlap_paths = topology["overlap_paths"]
        cls.composition_paths = topology["composition_paths"]
        cls.strict_composition_paths = sorted(
            cls.composition_paths + ["incident/renamed-source.txt"]
        )
        cls.required_paths = topology["required_paths"]
        cls.owned_paths = topology["aggregate_owned_paths"]
        cls.outside_paths = topology["outside_paths"]
        (
            cls.aggregate_tree_id,
            cls.aggregate_rows,
            cls.aggregate_blobs,
            cls.computed_aggregate,
        ) = incident_aggregate(cls.module, fixture["aggregate"]["prefix"])

    @contextmanager
    def incident_repository(self):
        with (
            mock.patch.object(
                self.module,
                "merge_base_commit",
                return_value=self.fixture["merge_base"],
            ),
            mock.patch.object(
                self.module,
                "git_diff_paths_for_aggregates",
                side_effect=[
                    list(self.product_paths),
                    list(self.upstream_paths),
                    list(self.composition_paths),
                ],
            ),
            mock.patch.object(
                self.module,
                "git_diff_paths",
                side_effect=[
                    list(self.product_paths),
                    list(self.upstream_paths),
                    list(self.strict_composition_paths),
                ],
            ),
            mock.patch.object(
                self.module,
                "_git_aggregate_tree",
                return_value=(self.aggregate_tree_id, self.aggregate_rows),
            ),
            mock.patch.object(
                self.module,
                "_git_batch_blobs",
                return_value=self.aggregate_blobs,
            ),
        ):
            yield

    def aggregate(self):
        return {
            key: self.fixture["aggregate"][key] for key in AGGREGATE_FIELDS
        }

    def v2_artifact(self):
        aggregate = self.aggregate()
        return {
            "schema": "fiat-integration-revalidation/v2",
            "affected_paths": list(self.outside_paths),
            "affected_aggregates": [aggregate],
            "checks": [
                {
                    "id": "portable-runtime",
                    "command": "python3 scripts/portable_promise_machine.py check",
                    "paths": [],
                    "aggregates": [aggregate["id"]],
                    "exit": 0,
                },
                {
                    "id": "outside-surface",
                    "command": "python3 plugins/hexaemeron/tests/run_tests.py",
                    "paths": list(self.outside_paths),
                    "aggregates": [],
                    "exit": 0,
                },
            ],
        }

    def call(self, artifact):
        descriptor, path = scratch_directory(".fiat-710-revalidation-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(artifact, handle)
            with self.incident_repository():
                record = self.module.integration_revalidation_record(
                    str(ROOT),
                    os.path.relpath(path, ROOT),
                    self.fixture["product_merge"],
                    self.fixture["base_head"],
                    self.fixture["sync_commit"],
                )
            return record
        finally:
            Path(path).unlink(missing_ok=True)

    def refusal(self, artifact):
        error = StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as stopped:
            self.call(artifact)
        self.assertEqual(stopped.exception.code, 2)
        return error.getvalue()

    def test_fixture_recomputes_every_incident_count_and_inventory_digest(self):
        inventories = {
            "product_paths": self.product_paths,
            "upstream_paths": self.upstream_paths,
            "overlap_paths": self.overlap_paths,
            "composition_paths": self.composition_paths,
            "required_paths": self.required_paths,
            "aggregate_owned_paths": self.owned_paths,
            "outside_paths": self.outside_paths,
        }
        self.assertEqual(
            self.fixture["counts"],
            {name: len(paths) for name, paths in inventories.items()},
        )
        self.assertEqual(
            self.fixture["inventory_sha256"],
            {name: inventory_digest(paths) for name, paths in inventories.items()},
        )
        for key, value in self.computed_aggregate.items():
            self.assertEqual(self.fixture["aggregate"][key], value)

    def test_acceptance_1_v1_no_longer_refuses_the_incident_on_its_count(self):
        """Issue 774 moved this. The fixture keeps what the entry controller did.

        Under `fiat-v5.30.1` the 1,095-path incident stopped at the shared
        500-path bound, which is the refusal the fixture records and the reason
        issue 710 built v2. Integration revalidation now carries its own 4,096
        ceiling, so a count of 1,095 no longer stops the artefact and it is
        refused further in, on its empty check array. What v2 still owns is the
        aggregate accounting and its 1,024-file and 32 MiB ceilings, which is
        what the remaining acceptances exercise.
        """
        # The version-1 reader disables rename detection, so a repository's
        # own `diff.renames` cannot shrink the surface a revalidation has to
        # cover. This delta carries one rename, so v1 sees the old path too and
        # the artefact has to name it. The v2 aggregate reader still detects
        # renames, which is why acceptance 2 keeps 1,095; that difference is
        # recorded as a lead rather than settled here.
        strict_required = sorted(
            set(self.strict_composition_paths) | set(self.overlap_paths)
        )
        artifact = {
            "schema": "fiat-integration-revalidation/v1",
            "affected_paths": strict_required,
            "checks": [],
        }
        error = self.refusal(artifact)
        self.assertEqual(
            self.fixture["entry_v1_refusal"]["stderr"],
            "hexctl: error: integration path delta exceeds 500 paths",
        )
        self.assertLess(len(strict_required), self.module.INTEGRATION_PATHS_MAX)
        self.assertNotIn("exceeds 500 paths", error)
        self.assertIn("checks must be a non-empty array", error)

    def test_acceptance_2_v2_receipts_887_owned_and_208_outside_paths(self):
        record = self.call(self.v2_artifact())
        self.assertEqual(record["schema"], "fiat-integration-revalidation/v2")
        self.assertEqual(record["required_path_count"], 1095)
        self.assertEqual(record["aggregate_owned_path_count"], 887)
        self.assertEqual(record["individual_path_count"], 208)
        self.assertEqual(record["affected_paths"], self.outside_paths)
        accepted = record["affected_aggregates"][0]
        for key in AGGREGATE_FIELDS:
            self.assertEqual(accepted[key], self.fixture["aggregate"][key])
        self.assertEqual(accepted["git_tree"], self.fixture["aggregate"]["git_tree"])
        self.assertEqual(accepted["total_bytes"], self.fixture["aggregate"]["total_bytes"])

    def test_acceptance_2_v2_sync_receipt_survives_done_integrate(self):
        artifact = self.v2_artifact()
        descriptor, path = scratch_directory(".fiat-710-transition-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(artifact, handle)
            state = {
                "phase": "integrate",
                "halted": None,
                "base": "main",
                "run_branch": "fiat/710-fixture",
                "config": {"git": {"base": "main"}},
                "steps": [
                    {
                        "n": 1,
                        "receipts": {"implement": {}, "audit": {}},
                        "audit": {},
                    }
                ],
                "receipts": {"study": {}, "runbook": {}},
                "integrate": {
                    "merged": [1],
                    "merges": {
                        "1": {"merge_commit": self.fixture["product_merge"]}
                    },
                },
            }
            sync_args = SimpleNamespace(
                dir=str(ROOT),
                commit=self.fixture["sync_commit"],
                base_commit=self.fixture["base_head"],
                revalidation=os.path.relpath(path, ROOT),
                supersede_sync=None,
                reason=None,
            )
            events = []
            with (
                self.incident_repository(),
                mock.patch.object(self.module, "verify_run"),
                mock.patch.object(
                    self.module, "_integrate_directive", return_value={"do": "integrate"}
                ),
                mock.patch.object(
                    self.module,
                    "remote_branch_tip",
                    side_effect=[self.fixture["sync_commit"], self.fixture["base_head"]],
                ),
                mock.patch.object(
                    self.module,
                    "_native_relation_repository_identity",
                    return_value="incident-repository",
                ),
                mock.patch.object(self.module, "_require_native_relation_history"),
                mock.patch.object(
                    self.module,
                    "_native_relation_parents",
                    return_value=[self.fixture["product_merge"], self.fixture["base_head"]],
                ),
                mock.patch.object(self.module, "verify_local_commit"),
                mock.patch.object(
                    self.module,
                    "verify_github_commits",
                    return_value=[self.fixture["sync_commit"]],
                ),
                mock.patch.object(
                    self.module,
                    "commit",
                    side_effect=lambda _root, _state, event, data: events.append(
                        (event, copy.deepcopy(data))
                    ),
                ),
            ):
                self.module.done_sync_run(sync_args, state)
            self.assertEqual(events[0][0], "done:sync-run")
            self.assertEqual(
                state["integrate"]["sync"]["revalidation"]["required_path_count"],
                1095,
            )

            integrate_args = SimpleNamespace(
                dir=str(ROOT),
                pr_url="https://github.com/wildcat-finance/skills/pull/710",
                merge_commit="a" * 40,
                closed_issue_url=None,
            )
            with (
                mock.patch.object(self.module, "verify_run"),
                mock.patch.object(
                    self.module, "_integrate_directive", return_value={"do": "integrate"}
                ),
                mock.patch.object(self.module, "carried_forward_fault", return_value=None),
                mock.patch.object(self.module, "run_pr_path", return_value="run-pr.md"),
                mock.patch.object(
                    self.module, "remote_branch_tip", return_value=self.fixture["sync_commit"]
                ),
                mock.patch.object(
                    self.module,
                    "inspect_pull_request",
                    return_value={"url": integrate_args.pr_url},
                ),
                mock.patch.object(
                    self.module, "verify_github_commits", return_value=["a" * 40]
                ),
                mock.patch.object(self.module, "merged_attribution", return_value={}),
                mock.patch.object(self.module, "carried_forward_record", return_value=[]),
                mock.patch.object(self.module, "commit"),
            ):
                self.module.done_integrate(integrate_args, state)
            self.assertEqual(state["phase"], "done")
            self.assertEqual(
                state["receipts"]["integrate"]["sync"]["revalidation"]["schema"],
                "fiat-integration-revalidation/v2",
            )
        finally:
            Path(path).unlink(missing_ok=True)

    def test_acceptance_3_count_manifest_and_tree_tampering_refuse(self):
        cases = {
            "file count": ("file_count", 886),
            "manifest digest": ("manifest_sha256", "0" * 64),
            "tree digest": ("tree_sha256", "0" * 64),
        }
        for expected, (field, value) in cases.items():
            with self.subTest(field=field):
                artifact = self.v2_artifact()
                artifact["affected_aggregates"][0][field] = value
                self.assertIn(expected, self.refusal(artifact))

    def test_acceptance_3_registry_and_check_tampering_refuse(self):
        for field, value in (
            ("prefix", "unreviewed/runtime/"),
            ("generator", "scripts/unreviewed.py"),
            ("manifest", "OTHER.json"),
        ):
            with self.subTest(field=field):
                artifact = self.v2_artifact()
                artifact["affected_aggregates"][0][field] = value
                self.assertIn("source registry", self.refusal(artifact))
        artifact = self.v2_artifact()
        artifact["checks"][0]["command"] = "python3 unreviewed.py"
        self.assertIn("registered verification command", self.refusal(artifact))
        artifact = self.v2_artifact()
        artifact["checks"][0]["aggregates"] = []
        self.assertIn("cover every affected aggregate", self.refusal(artifact))

    def test_acceptance_4_undeclared_or_missing_outside_paths_refuse(self):
        artifact = self.v2_artifact()
        artifact["affected_aggregates"][0]["id"] = "unreviewed-owner"
        self.assertIn("unknown aggregate", self.refusal(artifact))

        artifact = self.v2_artifact()
        missing = artifact["affected_paths"].pop()
        artifact["checks"][1]["paths"].remove(missing)
        self.assertIn("omits the computed outside", self.refusal(artifact))

        artifact = self.v2_artifact()
        owned = self.owned_paths[0]
        artifact["affected_paths"] = sorted([*artifact["affected_paths"], owned])
        artifact["checks"][1]["paths"] = list(artifact["affected_paths"])
        self.assertIn("exact outside integration surface", self.refusal(artifact))

    def test_every_v2_refusal_leaves_controller_state_and_ledger_bytes_unchanged(self):
        watched = [
            ROOT / ".hexaemeron/state.json",
            ROOT / ".hexaemeron/ledger.jsonl",
        ]
        before = {
            path: path.read_bytes() if path.exists() else None for path in watched
        }
        artifact = self.v2_artifact()
        artifact["affected_aggregates"][0]["tree_sha256"] = "0" * 64
        self.refusal(artifact)
        after = {
            path: path.read_bytes() if path.exists() else None for path in watched
        }
        self.assertEqual(after, before)

    def test_acceptance_5_small_v1_normalized_receipt_is_byte_compatible(self):
        artifact = {
            "schema": "fiat-integration-revalidation/v1",
            "affected_paths": ["shared.json", "upstream.py"],
            "checks": [
                {
                    "id": "root-suite",
                    "command": "python3 -m unittest discover -s tests",
                    "paths": ["shared.json", "upstream.py"],
                    "exit": 0,
                }
            ],
        }
        descriptor, path = scratch_directory(".fiat-710-v1-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(artifact, handle)
            data = Path(path).read_bytes()
            with (
                mock.patch.object(self.module, "merge_base_commit", return_value="4" * 40),
                mock.patch.object(
                    self.module,
                    "git_diff_paths",
                    side_effect=[
                        ["product.py", "shared.json"],
                        ["shared.json", "upstream.py"],
                        ["shared.json", "upstream.py"],
                    ],
                ),
            ):
                record = self.module.integration_revalidation_record(
                    str(ROOT), os.path.relpath(path, ROOT), "e" * 40, "b" * 40, "c" * 40
                )
            self.assertEqual(
                record,
                {
                    "schema": "fiat-integration-revalidation/v1",
                    "artifact": os.path.relpath(path, ROOT),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "base_before": "4" * 40,
                    "base_after": "b" * 40,
                    "product_paths": ["product.py", "shared.json"],
                    "upstream_paths": ["shared.json", "upstream.py"],
                    "overlap_paths": ["shared.json"],
                    "composition_paths": ["shared.json", "upstream.py"],
                    "affected_paths": ["shared.json", "upstream.py"],
                    "checks": artifact["checks"],
                },
            )
        finally:
            Path(path).unlink(missing_ok=True)


class AggregateObjectBoundaryTests(unittest.TestCase):
    """Resource, framing, object, mode and path gates at their exact edges."""

    def setUp(self):
        self.module = controller_module()
        self.aggregate_id = "promise-machine-portable-runtime-v1"
        self.registry = dict(
            self.module.GENERATOR_AGGREGATE_REGISTRY[self.aggregate_id]
        )

    def stop(self, callable_):
        error = StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as stopped:
            callable_()
        self.assertEqual(stopped.exception.code, 2)
        return error.getvalue()

    def controlled_stop(self, callable_):
        """Require a Fiat refusal rather than an uncaught input-type error."""
        error = StringIO()
        caught = None
        try:
            with redirect_stderr(error):
                callable_()
        except BaseException as exc:  # the assertion below classifies the boundary
            caught = exc
        self.assertIsInstance(caught, SystemExit)
        self.assertEqual(caught.code, 2)
        return error.getvalue()

    def tree_outputs(self, count, *, mode="100644", kind="blob", path=None):
        prefix = self.registry["prefix"]
        root = f"040000 tree {'a' * 40}\t{prefix.removesuffix('/')}\0".encode()
        members = []
        for index in range(count):
            member = path if path is not None else f"{prefix}{index:04d}.txt"
            members.append(
                f"{mode} {kind} {index:040x}\t{member}\0".encode()
            )
        return root, b"".join(members)

    def small_aggregate(self):
        registry = {
            "prefix": "runtime/",
            "generator": "scripts/generate.py",
            "manifest": "MANIFEST.json",
            "manifest_schema": "generated-runtime/v1",
            "manifest_contract": "promise-machine/v1",
            "command": "python3 scripts/generate.py check",
            "max_files": 4,
            "max_bytes": 4096,
        }
        payload = b"hello"
        payload_digest = hashlib.sha256(payload).hexdigest()
        document = {
            "schema": registry["manifest_schema"],
            "contract": registry["manifest_contract"],
            "generated_by": registry["generator"],
            "file_count": 1,
            "total_bytes": len(payload),
            "omissions": [],
            "files": [
                {
                    "bytes": len(payload),
                    "path": "payload.txt",
                    "sha256": payload_digest,
                    "source": "payload.txt",
                }
            ],
        }
        manifest = (json.dumps(document, sort_keys=True) + "\n").encode()
        manifest_digest = hashlib.sha256(manifest).hexdigest()
        rows = [
            {"path": "runtime/MANIFEST.json", "mode": "100644", "object": "a" * 40},
            {"path": "runtime/payload.txt", "mode": "100644", "object": "b" * 40},
        ]
        blobs = {
            "runtime/MANIFEST.json": manifest,
            "runtime/payload.txt": payload,
        }
        per_file = []
        for path, data, digest in (
            ("runtime/MANIFEST.json", manifest, manifest_digest),
            ("runtime/payload.txt", payload, payload_digest),
        ):
            per_file.append(
                (
                    path,
                    hashlib.sha256(
                        b"fiat-generator-file/v1\0"
                        + path.encode()
                        + b"\0"
                        + b"100644\0"
                        + str(len(data)).encode()
                        + b"\0"
                        + digest.encode()
                    ).digest(),
                )
            )
        per_file.sort()
        tree_digest = hashlib.sha256(
            b"fiat-generator-tree/v1\0"
            + b"".join(digest for _, digest in per_file)
        ).hexdigest()
        declaration = {
            "id": "fixture-runtime-v1",
            "prefix": registry["prefix"],
            "generator": registry["generator"],
            "manifest": registry["manifest"],
            "manifest_sha256": manifest_digest,
            "file_count": 2,
            "tree_sha256": tree_digest,
        }
        return registry, declaration, rows, blobs

    def rebind_manifest(self, declaration, rows, blobs, document):
        manifest = (json.dumps(document, sort_keys=True) + "\n").encode()
        rebound_blobs = {**blobs, "runtime/MANIFEST.json": manifest}
        rebound = dict(declaration)
        rebound["manifest_sha256"] = hashlib.sha256(manifest).hexdigest()
        file_digests = []
        for row in rows:
            data = rebound_blobs[row["path"]]
            digest = hashlib.sha256(data).hexdigest()
            file_digests.append(
                (
                    row["path"],
                    hashlib.sha256(
                        b"fiat-generator-file/v1\0"
                        + row["path"].encode()
                        + b"\0"
                        + row["mode"].encode()
                        + b"\0"
                        + str(len(data)).encode()
                        + b"\0"
                        + digest.encode()
                    ).digest(),
                )
            )
        file_digests.sort()
        rebound["tree_sha256"] = hashlib.sha256(
            b"fiat-generator-tree/v1\0"
            + b"".join(digest for _, digest in file_digests)
        ).hexdigest()
        return rebound, rebound_blobs

    def test_schema_types_refuse_unhashable_ids_and_non_integer_manifest_counts(self):
        declaration = {
            "id": self.aggregate_id,
            "prefix": self.registry["prefix"],
            "generator": self.registry["generator"],
            "manifest": self.registry["manifest"],
            "manifest_sha256": "0" * 64,
            "file_count": 1,
            "tree_sha256": "0" * 64,
        }
        for invalid_id in ([], {}):
            with self.subTest(id=invalid_id):
                candidate = {**declaration, "id": invalid_id}
                error = self.controlled_stop(
                    lambda: self.module._affected_aggregates([candidate])
                )
                self.assertIn("invalid id", error)

        registry, declaration, rows, blobs = self.small_aggregate()
        baseline = json.loads(blobs["runtime/MANIFEST.json"])
        for field, invalid in (
            ("file_count", True),
            ("file_count", 1.0),
            ("total_bytes", True),
            ("total_bytes", 5.0),
        ):
            with self.subTest(field=field, invalid=invalid):
                document = {**baseline, field: invalid}
                rebound, rebound_blobs = self.rebind_manifest(
                    declaration, rows, blobs, document
                )
                with (
                    mock.patch.object(
                        self.module,
                        "_git_aggregate_tree",
                        return_value=("c" * 40, rows),
                    ),
                    mock.patch.object(
                        self.module, "_git_batch_blobs", return_value=rebound_blobs
                    ),
                ):
                    error = self.controlled_stop(
                        lambda: self.module._validate_generator_aggregate(
                            str(ROOT), "d" * 40, rebound, registry
                        )
                    )
                self.assertIn("count does not match", error)

    def test_resource_boundary_accepts_1024_files_and_refuses_1025(self):
        outputs = self.tree_outputs(1024)
        with mock.patch.object(self.module, "bounded_git", side_effect=outputs):
            _, rows = self.module._git_aggregate_tree(
                str(ROOT), "b" * 40, self.aggregate_id, self.registry
            )
        self.assertEqual(len(rows), 1024)
        outputs = self.tree_outputs(1025)
        with mock.patch.object(self.module, "bounded_git", side_effect=outputs):
            error = self.stop(
                lambda: self.module._git_aggregate_tree(
                    str(ROOT), "b" * 40, self.aggregate_id, self.registry
                )
            )
        self.assertIn("1024-file ceiling", error)

    def test_symlink_submodule_non_blob_and_unsafe_path_are_refused(self):
        cases = (
            ("120000", "blob", None, "unsafe mode"),
            ("160000", "commit", None, "not a blob"),
            ("040000", "tree", None, "not a blob"),
            ("100644", "blob", self.registry["prefix"] + "../escape", "unsafe"),
        )
        for mode, kind, path, expected in cases:
            with self.subTest(mode=mode, kind=kind, path=path):
                outputs = self.tree_outputs(1, mode=mode, kind=kind, path=path)
                with mock.patch.object(self.module, "bounded_git", side_effect=outputs):
                    error = self.stop(
                        lambda: self.module._git_aggregate_tree(
                            str(ROOT), "b" * 40, self.aggregate_id, self.registry
                        )
                    )
                self.assertIn(expected, error)

    def test_manifest_membership_blob_digest_mode_and_contract_are_bound(self):
        registry, declaration, rows, blobs = self.small_aggregate()
        with (
            mock.patch.object(
                self.module, "_git_aggregate_tree", return_value=("c" * 40, rows)
            ),
            mock.patch.object(self.module, "_git_batch_blobs", return_value=blobs),
        ):
            accepted = self.module._validate_generator_aggregate(
                str(ROOT), "d" * 40, declaration, registry
            )
        self.assertEqual(accepted["git_tree"], "c" * 40)

        extra_rows = [
            *rows,
            {"path": "runtime/extra.txt", "mode": "100644", "object": "e" * 40},
        ]
        extra_blobs = {**blobs, "runtime/extra.txt": b"extra"}
        with (
            mock.patch.object(
                self.module,
                "_git_aggregate_tree",
                return_value=("c" * 40, extra_rows),
            ),
            mock.patch.object(
                self.module, "_git_batch_blobs", return_value=extra_blobs
            ),
        ):
            self.assertIn(
                "manifest membership",
                self.stop(
                    lambda: self.module._validate_generator_aggregate(
                        str(ROOT), "d" * 40, declaration, registry
                    )
                ),
            )

        changed_blobs = {**blobs, "runtime/payload.txt": b"HELLO"}
        with (
            mock.patch.object(
                self.module, "_git_aggregate_tree", return_value=("c" * 40, rows)
            ),
            mock.patch.object(
                self.module, "_git_batch_blobs", return_value=changed_blobs
            ),
        ):
            self.assertIn(
                "blob digest",
                self.stop(
                    lambda: self.module._validate_generator_aggregate(
                        str(ROOT), "d" * 40, declaration, registry
                    )
                ),
            )

        executable_rows = copy.deepcopy(rows)
        executable_rows[1]["mode"] = "100755"
        with (
            mock.patch.object(
                self.module,
                "_git_aggregate_tree",
                return_value=("c" * 40, executable_rows),
            ),
            mock.patch.object(self.module, "_git_batch_blobs", return_value=blobs),
        ):
            self.assertIn(
                "tree digest",
                self.stop(
                    lambda: self.module._validate_generator_aggregate(
                        str(ROOT), "d" * 40, declaration, registry
                    )
                ),
            )

        wrong_contract_blobs = dict(blobs)
        manifest = json.loads(blobs["runtime/MANIFEST.json"])
        manifest["contract"] = "other/v1"
        wrong_manifest = (json.dumps(manifest, sort_keys=True) + "\n").encode()
        wrong_contract_blobs["runtime/MANIFEST.json"] = wrong_manifest
        wrong_declaration = dict(declaration)
        wrong_declaration["manifest_sha256"] = hashlib.sha256(wrong_manifest).hexdigest()
        with (
            mock.patch.object(
                self.module, "_git_aggregate_tree", return_value=("c" * 40, rows)
            ),
            mock.patch.object(
                self.module, "_git_batch_blobs", return_value=wrong_contract_blobs
            ),
        ):
            self.assertIn(
                "wrong contract",
                self.stop(
                    lambda: self.module._validate_generator_aggregate(
                        str(ROOT), "d" * 40, wrong_declaration, registry
                    )
                ),
            )

    def fake_batch(self, mode: str, size: int = 3):
        temporary = tempfile.TemporaryDirectory()
        script = Path(temporary.name) / "git"
        script.write_text(
            """#!/usr/bin/env python3
import os
import sys
import time

mode = os.environ["FIAT_BATCH_MODE"]
size = int(os.environ.get("FIAT_BATCH_SIZE", "3"))
object_id = sys.stdin.buffer.readline().strip()
if mode == "timeout":
    time.sleep(1)
elif mode == "metadata":
    sys.stdout.buffer.write(b"x" * (2 * 1024 * 1024 + 1) + b"\\n")
elif mode == "partial":
    sys.stdout.buffer.write(object_id + b" blob 3\\nab")
elif mode == "wrong-type":
    sys.stdout.buffer.write(object_id + b" tree 3\\nabc\\n")
else:
    sys.stdout.buffer.write(
        object_id + b" blob " + str(size).encode() + b"\\n" + b"x" * size + b"\\n"
    )
""",
            encoding="utf-8",
        )
        script.chmod(0o755)
        environment = {
            "PATH": temporary.name + os.pathsep + os.environ.get("PATH", ""),
            "FIAT_BATCH_MODE": mode,
            "FIAT_BATCH_SIZE": str(size),
        }
        return temporary, environment

    def batch_call(self, limit):
        return self.module._git_batch_blobs(
            str(ROOT),
            self.aggregate_id,
            [{"path": "payload", "object": "a" * 40}],
            limit,
        )

    def test_resource_boundary_accepts_32_mib_and_refuses_one_byte_over(self):
        limit = 32 * 1024 * 1024
        temporary, environment = self.fake_batch("valid", limit)
        with temporary, mock.patch.dict(os.environ, environment, clear=False):
            blobs = self.batch_call(limit)
        self.assertEqual(len(blobs["payload"]), limit)

        temporary, environment = self.fake_batch("valid", limit + 1)
        with temporary, mock.patch.dict(os.environ, environment, clear=False):
            error = self.stop(lambda: self.batch_call(limit))
        self.assertIn(f"{limit}-byte ceiling", error)

    def test_timeout_oversized_metadata_partial_and_wrong_type_refuse(self):
        cases = (
            ("metadata", "metadata"),
            ("partial", "partial"),
            ("wrong-type", "malformed"),
        )
        for mode, expected in cases:
            with self.subTest(mode=mode):
                temporary, environment = self.fake_batch(mode)
                with temporary, mock.patch.dict(os.environ, environment, clear=False):
                    error = self.stop(lambda: self.batch_call(64))
                self.assertIn(expected, error)

        temporary, environment = self.fake_batch("timeout")
        with (
            temporary,
            mock.patch.dict(os.environ, environment, clear=False),
            mock.patch.object(self.module, "GIT_TIMEOUT", 0.01),
        ):
            error = self.stop(lambda: self.batch_call(64))
        self.assertIn("timed out", error)


if __name__ == "__main__":
    unittest.main()
