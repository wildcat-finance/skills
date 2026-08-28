"""Focused guards for the artifact-anchored issue-622 bootstrap."""

import ast
import copy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import time
import unittest
from unittest import mock
import zlib


ROOT = Path(__file__).resolve().parents[3]
VERIFIER = ROOT / "scripts" / "verify_issue_622_inoculation.py"
RECORD = ROOT / "tests" / "fixtures" / "issue-622-inoculation-v1.json"
CURRENT_EXTENSION_CAUSE_ID = "inoculation-elenchus-packet-independence"
ROUND_SIX_CAUSE_ID = "guard-discovery-method-outcome-probe"
ROUND_EIGHT_CAUSE_IDS = {
    "fixture-domain-inherited-cleanup-registration",
    "fixture-domain-unresolved-class-cleanup-target",
    "promise-reporter-release-surface-binding",
}


class _MissingVerifier:
    """Keep the exact-parent overlay assertion-red when the verifier is new."""

    def __getattr__(self, name):
        raise AssertionError(
            "cumulative verifier feature is absent on this parent: "
            "scripts/verify_issue_622_inoculation.py"
        )


if VERIFIER.is_file():
    spec = importlib.util.spec_from_file_location(
        "verify_issue_622_inoculation", VERIFIER
    )
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
else:
    verifier = _MissingVerifier()


def require_verifier_features(case, *names):
    """Make a missing parent interface assertion-red rather than error-red."""
    missing = [name for name in names if not hasattr(verifier, name)]
    case.assertEqual([], missing, f"verifier is missing audit interfaces: {missing}")


class Issue622InoculationCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(RECORD.read_text(encoding="utf-8"))

    @staticmethod
    def record_path(source, target=None):
        return {
            "source": source,
            "target": source if target is None else target,
            "archive_sha256": "0" * 64,
            "current_sha256": "1" * 64,
        }

    @staticmethod
    def transform():
        return [{
            "id": verifier.TRANSFORM_ID,
            "source": verifier.ADR_SOURCE,
            "target": verifier.ADR_TARGET,
        }]

    def test_current_extension_is_packet_independent_and_elenchus_guarded(self):
        self.assertTrue(
            VERIFIER.is_file(),
            "cumulative verifier feature is absent on this parent: "
            "scripts/verify_issue_622_inoculation.py",
        )
        require_verifier_features(
            self,
            "EXPECTED_PACKET_CAUSES",
            "EXPECTED_CURRENT_CAUSES",
            "current_target_identity_mismatches",
        )
        self.assertIn(
            CURRENT_EXTENSION_CAUSE_ID,
            verifier.EXPECTED_CURRENT_CAUSES,
        )
        source = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        packet_names = [
            node for node in ast.walk(source)
            if isinstance(node, ast.Name) and node.id == "PACKET"
        ]
        self.assertEqual([], packet_names)
        packet_literal_prefix = "622-" + "CARRYOVER"
        packet_literals = [
            node.value for node in ast.walk(source)
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and packet_literal_prefix in node.value
            )
        ]
        self.assertEqual([], packet_literals)

    def test_promise_reporter_release_surface_binds_current_runner(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        reporter = coverage["run_observation_binding"]["reporter"]
        self.assertEqual(
            "plugins/hexaemeron/tests/run_tests.py", reporter["path"]
        )
        self.assertEqual(
            hashlib.sha256((ROOT / reporter["path"]).read_bytes()).hexdigest(),
            reporter["sha256"],
        )

    def test_checked_in_record_binds_current_targets_and_guard_ast(self):
        if CURRENT_EXTENSION_CAUSE_ID not in getattr(
            verifier, "EXPECTED_CURRENT_CAUSES", {}
        ):
            self.skipTest(
                "Elenchus parent has the predecessor verifier contract"
            )
        if ROUND_SIX_CAUSE_ID not in verifier.EXPECTED_CURRENT_CAUSES:
            self.skipTest(
                "Elenchus parent has the round-5 verifier contract"
            )
        require_verifier_features(
            self, "GUARD_PATH_BY_OWNER", "EXPECTED_GUARD_SHA256"
        )
        record_causes = {
            item["id"] for item in self.record["current_cause_guards"]
        }
        predecessor_cause_sets = ({
            "descendant-output-descriptor-lifetime",
            "unexpected-success-non-green",
            "fixture-blocked-unittest-accounting",
            "inoculation-target-self-authorisation",
            "inoculation-guard-discoverability",
        }, {
            "automatic-capacity-safety-cap",
            "detached-descendant-boundary",
            "descendant-output-descriptor-lifetime",
            "unexpected-success-non-green",
            "fixture-blocked-unittest-accounting",
            "fixture-skip-origin-binding",
            "guard-discovery-static-proof",
            "inoculation-target-self-authorisation",
            "inoculation-guard-discoverability",
        }, {
            "automatic-capacity-safety-cap",
            "custom-suite-execution-semantics",
            "detached-descendant-boundary",
            "descendant-output-descriptor-lifetime",
            "unexpected-success-non-green",
            "fixture-blocked-unittest-accounting",
            "fixture-skip-origin-binding",
            "guard-discovery-static-proof",
            "guard-discovery-control-flow-proof",
            "inoculation-bounded-read-inode-binding",
            "inoculation-target-self-authorisation",
            "inoculation-guard-discoverability",
            "worker-process-group-identity-lifetime",
        }, {
            "archive-git-replace-substitution",
            "automatic-capacity-safety-cap",
            "custom-suite-execution-semantics",
            "detached-descendant-boundary",
            "descendant-output-descriptor-lifetime",
            "unexpected-success-non-green",
            "fixture-blocked-unittest-accounting",
            "fixture-domain-sharding-semantics",
            "fixture-skip-origin-binding",
            "guard-discovery-static-proof",
            "guard-discovery-control-flow-proof",
            "guard-discovery-namespace-proof",
            "inoculation-bounded-read-inode-binding",
            "inoculation-target-self-authorisation",
            "inoculation-guard-discoverability",
            "worker-process-group-identity-lifetime",
            "current-base-adr-number-uniqueness",
            "worker-protocol-checkout-interference",
        }, {
            "archive-git-replace-substitution",
            "automatic-capacity-safety-cap",
            "cgroup-v2-membership-quota-resolution",
            "current-base-adr-number-uniqueness",
            "custom-suite-execution-semantics",
            "detached-descendant-boundary",
            "descendant-output-descriptor-lifetime",
            "fixture-blocked-unittest-accounting",
            "fixture-domain-sharding-semantics",
            "fixture-domain-worker-rediscovery-binding",
            "fixture-skip-origin-binding",
            "guard-discovery-control-flow-proof",
            "guard-discovery-namespace-proof",
            "guard-discovery-runtime-mutation-proof",
            "guard-discovery-static-proof",
            "inoculation-bounded-read-content-binding",
            "inoculation-bounded-read-inode-binding",
            "inoculation-guard-discoverability",
            "inoculation-target-self-authorisation",
            "unexpected-success-non-green",
            "worker-process-group-identity-lifetime",
            "worker-protocol-checkout-interference",
        }, {
            "archive-git-replace-substitution",
            "automatic-capacity-safety-cap",
            "cgroup-v1-membership-quota-resolution",
            "cgroup-v2-membership-quota-resolution",
            "current-base-adr-number-uniqueness",
            "custom-suite-execution-semantics",
            "custom-suite-metaclass-attribute-proof",
            "detached-descendant-boundary",
            "descendant-output-descriptor-lifetime",
            "fixture-blocked-unittest-accounting",
            "fixture-domain-dynamic-lookup-proof",
            "fixture-domain-sharding-semantics",
            "fixture-domain-worker-rediscovery-binding",
            "fixture-skip-origin-binding",
            "guard-discovery-control-flow-proof",
            "guard-discovery-module-namespace-mutation",
            "guard-discovery-namespace-proof",
            "guard-discovery-runtime-mutation-proof",
            "guard-discovery-static-proof",
            "inoculation-bounded-read-content-binding",
            "inoculation-bounded-read-inode-binding",
            "inoculation-guard-discoverability",
            "inoculation-target-self-authorisation",
            "unexpected-success-non-green",
            "worker-process-group-identity-lifetime",
            "worker-protocol-checkout-interference",
        }, {
            "archive-git-replace-substitution",
            "automatic-capacity-safety-cap",
            "cgroup-v1-membership-quota-resolution",
            "cgroup-v2-membership-quota-resolution",
            "cgroup-v2-mount-root-quota-resolution",
            "current-base-adr-number-uniqueness",
            "custom-suite-execution-semantics",
            "custom-suite-fixture-transition-hooks",
            "custom-suite-metaclass-attribute-proof",
            "detached-descendant-boundary",
            "descendant-output-descriptor-lifetime",
            "fixture-blocked-unittest-accounting",
            "fixture-domain-class-descriptor-proof",
            "fixture-domain-dynamic-lookup-proof",
            "fixture-domain-sharding-semantics",
            "fixture-domain-worker-rediscovery-binding",
            "fixture-skip-origin-binding",
            "guard-discovery-control-flow-proof",
            "guard-discovery-import-time-helper-mutation",
            "guard-discovery-module-namespace-mutation",
            "guard-discovery-namespace-proof",
            "guard-discovery-runtime-mutation-proof",
            "guard-discovery-static-proof",
            "inoculation-bounded-read-content-binding",
            "inoculation-bounded-read-inode-binding",
            "inoculation-guard-discoverability",
            "inoculation-target-self-authorisation",
            "unexpected-success-non-green",
            "worker-process-group-identity-lifetime",
            "worker-protocol-checkout-interference",
        }, record_causes - ROUND_EIGHT_CAUSE_IDS)
        if any(
            set(verifier.EXPECTED_CURRENT_CAUSES) == predecessor_causes
            and predecessor_causes <= record_causes
            for predecessor_causes in predecessor_cause_sets
        ):
            self.skipTest(
                "Elenchus parent has the predecessor verifier contract"
            )
        verifier.validate_record_shape(self.record)
        findings = verifier.normalize_findings(
            self.record["findings"], "record findings"
        )
        causes = verifier.normalize_findings(
            self.record["current_cause_guards"], "current cause guards"
        )
        paths = {
            item["source"]: item for item in self.record["paths"]
        }
        if not hasattr(verifier, "current_target_identity_mismatches"):
            self.skipTest(
                "Elenchus parent cannot classify a newer target contract"
            )
        if verifier.current_target_identity_mismatches(paths):
            self.skipTest(
                "Elenchus parent has an older target-identity contract"
            )

        verifier.verify_current_targets(ROOT, paths)
        guard_digests = dict(verifier.EXPECTED_GUARD_SHA256)
        guard_digests[verifier.INOCULATION_GUARD_PATH] = hashlib.sha256(
            (ROOT / verifier.INOCULATION_GUARD_PATH).read_bytes()
        ).hexdigest()
        with mock.patch.object(
            verifier, "EXPECTED_GUARD_SHA256", guard_digests
        ):
            guards = verifier.verify_guard_names(ROOT, findings, causes)

        self.assertEqual(18, len(paths))
        self.assertEqual(23, len(findings))
        self.assertEqual(60, len(causes))
        self.assertEqual(13, len(self.record["families"]))
        self.assertEqual(9, len(verifier.ADDITIONAL_CURRENT_PATHS))
        self.assertEqual(101, len(guards))

    def test_guard_identity_dependency_is_explicit_for_parent_overlay(self):
        parameters = inspect.signature(verifier.verify_guard_names).parameters
        self.assertIn(
            "expected_guard_sha256",
            parameters,
            "guard identity cannot be rebound for an exact-parent test overlay",
        )
        guard_path = verifier.INOCULATION_GUARD_PATH
        source = textwrap.dedent("""
            import unittest

            class Guard(unittest.TestCase):
                def test_required_guard(self):
                    pass
        """).encode("utf-8")
        findings = {
            "synthetic": {
                "owner": verifier.VERIFIER_PATH,
                "guards": ["test_required_guard"],
                "family": "discovery-boundary",
            }
        }
        with tempfile.TemporaryDirectory(
            prefix="inoculation-guard-overlay-"
        ) as raw:
            root = Path(raw)
            target = root / guard_path
            target.parent.mkdir(parents=True)
            target.write_bytes(source)
            guards = verifier.verify_guard_names(
                root,
                findings,
                {},
                expected_guard_sha256={
                    guard_path: hashlib.sha256(source).hexdigest()
                },
            )
        self.assertEqual({"test_required_guard"}, guards)

    def test_recorded_carryover_findings_distinguish_product_and_guard_owners(self):
        findings = verifier.normalize_findings(
            self.record["findings"], "record findings"
        )

        self.assertEqual(23, len(findings))
        self.assertEqual(
            {verifier.RUNNER_PATH},
            {finding["owner"] for finding in findings.values()},
        )
        self.assertEqual(
            verifier.PARALLEL_GUARD_PATH,
            verifier.GUARD_PATH_BY_OWNER[verifier.RUNNER_PATH],
        )

    def test_substituted_artifact_cannot_self_authorise_through_the_record(self):
        substituted = b"substituted packet"
        record = copy.deepcopy(self.record)
        record["artifacts"]["packet"]["sha256"] = hashlib.sha256(
            substituted
        ).hexdigest()

        with self.assertRaisesRegex(
            verifier.InoculationError, "packet SHA-256"
        ):
            verifier.artifact_digests(
                substituted,
                b"substituted patch",
                record,
            )

    def test_bounded_read_cannot_switch_inodes_between_check_and_open(self):
        with tempfile.TemporaryDirectory(prefix="inoculation-read-") as raw:
            root = Path(raw)
            target = root / "record.json"
            backup = root / "record.saved"
            outside = root / "outside.json"
            target.write_bytes(b"trusted!")
            outside.write_bytes(b"hostile!")
            original_open = verifier.os.open
            swapped = False

            def racing_open(path, *args, **kwargs):
                nonlocal swapped
                if os.fspath(path) == os.fspath(target) and not swapped:
                    swapped = True
                    target.rename(backup)
                    target.symlink_to(outside)
                    try:
                        return original_open(path, *args, **kwargs)
                    finally:
                        target.unlink()
                        backup.rename(target)
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(verifier.os, "open", racing_open),
                self.assertRaisesRegex(
                    verifier.InoculationError, "is unavailable"
                ),
            ):
                verifier.bounded_regular_bytes(target, 64, "diagnostic record")

            self.assertTrue(swapped)
            self.assertEqual(b"trusted!", target.read_bytes())

    def test_bounded_read_refuses_regular_inode_switch_before_open(self):
        with tempfile.TemporaryDirectory(prefix="inoculation-inode-") as raw:
            root = Path(raw)
            target = root / "record.json"
            trusted = root / "record.saved"
            hostile = root / "hostile.json"
            target.write_bytes(b"trusted!")
            hostile.write_bytes(b"hostile!")
            original_open = verifier.os.open
            swapped = False

            def racing_open(path, *args, **kwargs):
                nonlocal swapped
                if os.fspath(path) == os.fspath(target) and not swapped:
                    swapped = True
                    target.rename(trusted)
                    hostile.rename(target)
                    try:
                        return original_open(path, *args, **kwargs)
                    finally:
                        target.rename(hostile)
                        trusted.rename(target)
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(verifier.os, "open", racing_open),
                self.assertRaisesRegex(
                    verifier.InoculationError,
                    "changed before it was opened",
                ),
            ):
                verifier.bounded_regular_bytes(target, 64, "diagnostic record")

            self.assertTrue(swapped)
            self.assertEqual(b"trusted!", target.read_bytes())
            self.assertEqual(b"hostile!", hostile.read_bytes())

    def test_bounded_read_detects_in_place_content_substitution(self):
        with tempfile.TemporaryDirectory(prefix="inoculation-content-") as raw:
            target = Path(raw) / "record.json"
            target.write_bytes(b"original")
            before = target.stat()
            real_read = verifier.os.read
            swapped = False

            def racing_read(file_descriptor, maximum):
                nonlocal swapped
                if not swapped:
                    swapped = True
                    with target.open("r+b", buffering=0) as stream:
                        stream.write(b"hostile!")
                    os.utime(
                        target,
                        ns=(before.st_atime_ns, before.st_mtime_ns),
                    )
                return real_read(file_descriptor, maximum)

            with (
                mock.patch.object(verifier.os, "read", racing_read),
                self.assertRaisesRegex(
                    verifier.InoculationError, "changed while it was read"
                ),
            ):
                verifier.bounded_regular_bytes(
                    target, 64, "diagnostic record"
                )

    def test_missing_and_additional_record_paths_are_refused(self):
        packet_paths = [verifier.ADR_SOURCE, "tests/example.py"]
        valid = [
            self.record_path(verifier.ADR_SOURCE, verifier.ADR_TARGET),
            self.record_path("tests/example.py"),
        ]

        for label, paths in (
            ("missing", valid[:-1]),
            ("additional", valid + [self.record_path("tests/extra.py")]),
        ):
            with self.subTest(label=label), self.assertRaisesRegex(
                verifier.InoculationError, "record path set mismatch"
            ):
                verifier.validate_path_map(
                    paths, packet_paths, self.transform()
                )

    def test_packet_and_patch_path_disagreement_is_refused(self):
        packet_paths = [verifier.ADR_SOURCE, "tests/example.py"]

        with self.assertRaisesRegex(
            verifier.InoculationError,
            "packet and patch current path inventories disagree",
        ):
            verifier.validate_cumulative_path_set(
                packet_paths,
                [verifier.ADR_SOURCE, "tests/different.py"],
            )

    def test_duplicate_target_is_refused(self):
        packet_paths = [verifier.ADR_SOURCE, "tests/example.py"]
        record_paths = [
            self.record_path(verifier.ADR_SOURCE, verifier.ADR_TARGET),
            self.record_path("tests/example.py", verifier.ADR_TARGET),
        ]

        with self.assertRaisesRegex(
            verifier.InoculationError, "duplicate target"
        ):
            verifier.validate_path_map(
                record_paths,
                packet_paths,
                self.transform(),
            )

    def test_only_the_declared_adr_transform_is_accepted(self):
        bad = self.transform()
        bad[0]["target"] = "docs/decisions/ADR-999.md"

        with self.assertRaisesRegex(
            verifier.InoculationError, "accepted ADR move"
        ):
            verifier.validate_transform_list(bad)

    def test_missing_current_guard_is_refused_by_ast_name(self):
        if CURRENT_EXTENSION_CAUSE_ID not in getattr(
            verifier, "EXPECTED_CURRENT_CAUSES", {}
        ):
            self.skipTest(
                "Elenchus parent has the predecessor verifier contract"
            )
        findings = {
            "synthetic": {
                "owner": verifier.RUNNER_PATH,
                "guards": ["test_guard_that_does_not_exist"],
                "family": "bounded-output",
            }
        }
        guard_path = verifier.GUARD_PATH_BY_OWNER[verifier.RUNNER_PATH]
        guard_digests = dict(verifier.EXPECTED_GUARD_SHA256)
        guard_digests[guard_path] = hashlib.sha256(
            (ROOT / guard_path).read_bytes()
        ).hexdigest()

        with (
            mock.patch.object(
                verifier, "EXPECTED_GUARD_SHA256", guard_digests
            ),
            self.assertRaisesRegex(
                verifier.InoculationError, "current guard is missing"
            ),
        ):
            verifier.verify_guard_names(ROOT, findings, {})

    def test_unknown_family_is_refused(self):
        values = [{
            "id": "synthetic",
            "owner": verifier.RUNNER_PATH,
            "guards": ["test_unexpected_success_is_non_green"],
            "family": "invented-family",
        }]

        with self.assertRaisesRegex(
            verifier.InoculationError, "unknown family"
        ):
            verifier.normalize_findings(values, "synthetic findings")

    def test_changed_current_content_is_refused(self):
        paths = {
            item["source"]: copy.deepcopy(item)
            for item in self.record["paths"]
        }
        first = next(iter(paths.values()))
        target = first["target"]
        real_target_bytes = verifier.target_bytes

        def changed_target(root, relative):
            if relative == target:
                return b"changed current target\n"
            return real_target_bytes(root, relative)

        with (
            mock.patch.object(
                verifier, "target_bytes", side_effect=changed_target
            ),
            self.assertRaisesRegex(
                verifier.InoculationError, "current target content mismatch"
            ),
        ):
            verifier.verify_current_targets(ROOT, paths)

    def test_paired_current_target_and_record_substitution_is_refused(self):
        paths = {
            item["source"]: copy.deepcopy(item)
            for item in self.record["paths"]
        }
        first = next(iter(paths.values()))
        target = first["target"]
        substituted = b"paired target and record substitution\n"
        first["current_sha256"] = hashlib.sha256(substituted).hexdigest()
        real_target_bytes = verifier.target_bytes

        def paired_target(root, relative):
            if relative == target:
                return substituted
            return real_target_bytes(root, relative)

        with (
            mock.patch.object(
                verifier, "target_bytes", side_effect=paired_target
            ),
            self.assertRaisesRegex(
                verifier.InoculationError,
                "record current content identity mismatch",
            ),
        ):
            verifier.verify_current_targets(ROOT, paths)

    def test_cumulative_current_target_substitution_is_refused(self):
        trusted = b"trusted cumulative target\n"
        substituted = b"substituted cumulative target\n"
        path = "tests/cumulative-example.txt"
        inventory = {path: hashlib.sha256(trusted).hexdigest()}

        with (
            mock.patch.object(
                verifier, "EXPECTED_CUMULATIVE_REBIND_SHA256", {}
            ),
            mock.patch.object(
                verifier, "target_bytes", return_value=substituted
            ),
            self.assertRaisesRegex(
                verifier.InoculationError,
                "cumulative current target content mismatch",
            ),
        ):
            verifier.verify_cumulative_targets(ROOT, inventory)

    def test_archive_reads_ignore_local_git_replace_objects(self):
        with tempfile.TemporaryDirectory(prefix="inoculation-replace-") as raw:
            root = Path(raw)
            subprocess.run(
                ["git", "init", "-q"], cwd=root, check=True
            )

            def store(payload):
                return subprocess.run(
                    ["git", "hash-object", "-w", "--stdin"],
                    cwd=root,
                    input=payload,
                    stdout=subprocess.PIPE,
                    check=True,
                ).stdout.decode("ascii").strip()

            original = store(b"original archive bytes\n")
            replacement = store(b"replacement archive bytes\n")
            subprocess.run(
                ["git", "replace", original, replacement],
                cwd=root,
                check=True,
            )

            completed = verifier.git_run(
                root,
                ["cat-file", "blob", original],
                "replace-object guard",
            )

        self.assertEqual(b"original archive bytes\n", completed.stdout)

    def test_archive_object_reads_recompute_git_identity(self):
        require_verifier_features(self, "git_object_bytes")
        with tempfile.TemporaryDirectory(prefix="inoculation-object-") as raw:
            root = Path(raw)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            original = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"],
                cwd=root,
                input=b"original archive bytes\n",
                stdout=subprocess.PIPE,
                check=True,
            ).stdout.decode("ascii").strip()
            substituted = b"substituted archive bytes\n"
            loose = root / ".git" / "objects" / original[:2] / original[2:]
            loose.chmod(0o600)
            loose.write_bytes(
                zlib.compress(
                    f"blob {len(substituted)}\0".encode("ascii")
                    + substituted
                )
            )

            with self.assertRaisesRegex(
                verifier.InoculationError, "Git object identity mismatch"
            ):
                verifier.git_object_bytes(
                    root,
                    original,
                    "blob",
                    verifier.MAX_TARGET_BYTES,
                    "archive object",
                )

    def test_deep_record_json_is_a_stable_refusal(self):
        with tempfile.TemporaryDirectory(prefix="inoculation-record-") as raw:
            record = Path(raw) / "record.json"
            record.write_bytes(b"{}")
            with mock.patch.object(
                verifier.json,
                "loads",
                side_effect=RecursionError("hostile JSON nesting"),
            ):
                try:
                    verifier.load_record(record)
                except verifier.InoculationError as error:
                    self.assertIn("record is not valid", str(error))
                except RecursionError as error:
                    self.fail(f"record JSON recursion escaped: {error}")
                else:
                    self.fail("resource-hostile record JSON was accepted")

    def test_required_guard_must_be_one_discovered_unittest_case(self):
        findings = {
            "synthetic": {
                "owner": verifier.RUNNER_PATH,
                "guards": ["test_unexpected_success_is_non_green"],
                "family": "unittest-outcomes",
            }
        }
        no_op = (
            b"def test_unexpected_success_is_non_green():\n"
            b"    pass\n"
        )
        guard_path = getattr(
            verifier,
            "PARALLEL_GUARD_PATH",
            getattr(
                verifier,
                "GUARD_PATH",
                "plugins/hexaemeron/tests/test_parallel_test_runner.py",
            ),
        )
        guard_digests = {
            guard_path: hashlib.sha256(no_op).hexdigest()
        }

        with (
            mock.patch.object(
                verifier,
                "EXPECTED_GUARD_SHA256",
                guard_digests,
                create=True,
            ),
            mock.patch.object(verifier, "target_bytes", return_value=no_op),
            self.assertRaisesRegex(
                verifier.InoculationError,
                "not one discovered unittest case",
            ),
        ):
            verifier.verify_guard_names(ROOT, findings, {})

    def test_guard_verification_rejects_import_time_decorator_erasure(self):
        findings = {
            "synthetic": {
                "owner": verifier.VERIFIER_PATH,
                "guards": ["test_required_guard"],
                "family": "discovery-boundary",
            }
        }
        guard_path = verifier.INOCULATION_GUARD_PATH
        sources = {
            "erased": """
                import unittest

                class Guard(unittest.TestCase):
                    def test_required_guard(self): pass

                def erase_guard(target):
                    del Guard.test_required_guard
                    return target

                @erase_guard
                class Unrelated:
                    pass
            """,
            "spoofed-method-name": """
                import unittest

                class Guard(unittest.TestCase):
                    def __getattribute__(self, name):
                        if name == "_testMethodName":
                            return "test_required_guard"
                        return super().__getattribute__(name)

                    def test_required_guard(self): pass
                    def test_decoy(self): pass

                def erase_guard(target):
                    del Guard.test_required_guard
                    return target

                @erase_guard
                class Unrelated:
                    pass
            """,
        }

        for label, raw_source in sources.items():
            with self.subTest(runtime_shape=label), tempfile.TemporaryDirectory(
                prefix="inoculation-runtime-discovery-"
            ) as raw:
                source = textwrap.dedent(raw_source).encode("utf-8")
                root = Path(raw)
                target = root / guard_path
                target.parent.mkdir(parents=True)
                target.write_bytes(source)
                with (
                    mock.patch.object(
                        verifier,
                        "EXPECTED_GUARD_SHA256",
                        {guard_path: hashlib.sha256(source).hexdigest()},
                    ),
                    self.assertRaisesRegex(
                        verifier.InoculationError,
                        "runtime unittest discovery",
                    ),
                ):
                    verifier.verify_guard_names(root, findings, {})

    def test_runtime_discovery_result_drain_ignores_inherited_writer(self):
        if not hasattr(os, "fork"):
            self.skipTest("inherited descriptor probe requires os.fork")
        guard_path = verifier.INOCULATION_GUARD_PATH
        source = textwrap.dedent("""
            import os
            import time
            import unittest

            child = os.fork()
            if child == 0:
                time.sleep(2)
                os._exit(0)

            class Guard(unittest.TestCase):
                def test_required_guard(self): pass
        """).encode("utf-8")
        with tempfile.TemporaryDirectory(
            prefix="inoculation-runtime-writer-"
        ) as raw:
            root = Path(raw)
            target = root / guard_path
            target.parent.mkdir(parents=True)
            target.write_bytes(source)
            started = time.monotonic()
            with mock.patch.object(
                verifier, "RUNTIME_DISCOVERY_TIMEOUT_SECONDS", 1
            ):
                discovered = verifier.runtime_unittest_methods(
                    root,
                    guard_path,
                    source,
                    {"test_required_guard"},
                )
            elapsed = time.monotonic() - started

        self.assertEqual(1, discovered["test_required_guard"])
        self.assertLess(
            elapsed,
            1.5,
            "a descendant retaining the result writer defeated the bound",
        )

    def test_guard_ast_proof_refuses_runtime_discovery_decoys(self):
        require_verifier_features(self, "unittest_methods")

        def methods(source):
            return verifier.unittest_methods(
                ast.parse(textwrap.dedent(source))
            )

        aliases = methods("""
            import unittest as unit
            from unittest import TestCase as Case

            class ModuleAlias(unit.TestCase):
                def test_module_alias(self): pass

            class ImportedAlias(Case):
                def test_imported_alias(self): pass
        """)
        self.assertEqual(1, aliases["test_module_alias"])
        self.assertEqual(1, aliases["test_imported_alias"])

        inherited = methods("""
            from unittest import TestCase as Case

            class Parent(Case):
                def test_inherited_guard(self): pass

            class Child(Parent):
                pass
        """)
        self.assertEqual(2, inherited["test_inherited_guard"])

        nested = methods("""
            import unittest

            class Holder:
                class Hidden(unittest.TestCase):
                    def test_nested_guard(self): pass
        """)
        self.assertEqual(0, nested["test_nested_guard"])

        hostile = {
            "load-tests": (
                "dynamic unittest discovery hook",
                """
                    import unittest
                    class Guard(unittest.TestCase):
                        def test_guard(self): pass
                    def load_tests(loader, standard, pattern):
                        return unittest.TestSuite()
                """,
            ),
            "decorator": (
                "decorates a test method",
                """
                    import unittest
                    def erase(function): return None
                    class Guard(unittest.TestCase):
                        @erase
                        def test_guard(self): pass
                """,
            ),
            "duplicate-class": (
                "repeats a top-level class binding",
                """
                    import unittest
                    class Guard(unittest.TestCase):
                        def test_guard(self): pass
                    class Guard(unittest.TestCase):
                        def test_other(self): pass
                """,
            ),
            "class-alias": (
                "aliases a discovered TestCase binding",
                """
                    import unittest
                    class Guard(unittest.TestCase):
                        def test_guard(self): pass
                    GuardAgain = Guard
                """,
            ),
        }
        for label, (message, source) in hostile.items():
            with self.subTest(case=label), self.assertRaisesRegex(
                verifier.InoculationError, message
            ):
                methods(source)

    def test_guard_ast_refuses_custom_testcase_execution_entrypoints(self):
        require_verifier_features(self, "unittest_methods")
        hostile = {
            "run": """
                import unittest

                class Guard(unittest.TestCase):
                    def run(self, result=None):
                        return result or unittest.TestResult()

                    def test_required_guard(self): pass
            """,
            "__call__": """
                import unittest

                class Guard(unittest.TestCase):
                    def __call__(self, result=None):
                        return result or unittest.TestResult()

                    def test_required_guard(self): pass
            """,
        }
        for entrypoint, source in hostile.items():
            with self.subTest(entrypoint=entrypoint), self.assertRaisesRegex(
                verifier.InoculationError,
                "custom TestCase execution entrypoint",
            ):
                verifier.unittest_methods(ast.parse(textwrap.dedent(source)))

    def test_guard_ast_refuses_custom_testcase_method_dispatch(self):
        require_verifier_features(self, "unittest_methods")
        source = """
            import unittest

            class Guard(unittest.TestCase):
                def _callTestMethod(self, method):
                    if getattr(method, "__name__", "") == "sentinel":
                        method()

                def test_required_guard(self):
                    raise AssertionError("original guard ran")
        """

        with self.assertRaisesRegex(
            verifier.InoculationError,
            "custom TestCase method dispatch",
        ):
            verifier.unittest_methods(ast.parse(textwrap.dedent(source)))

    def test_runtime_guard_probe_refuses_fixture_skipped_method(self):
        require_verifier_features(self, "runtime_unittest_methods")
        guard_path = verifier.INOCULATION_GUARD_PATH
        source = textwrap.dedent("""
            import unittest

            class Guard(unittest.TestCase):
                @classmethod
                def setUpClass(cls):
                    raise unittest.SkipTest("disabled guard class")

                def test_required_guard(self):
                    raise AssertionError("red sentinel")
        """).encode("utf-8")
        with tempfile.TemporaryDirectory(
            prefix="inoculation-runtime-fixture-skip-"
        ) as raw:
            root = Path(raw)
            target = root / guard_path
            target.parent.mkdir(parents=True)
            target.write_bytes(source)
            with self.assertRaisesRegex(
                verifier.InoculationError,
                "execution probe was not complete",
            ):
                verifier.runtime_unittest_methods(
                    root,
                    guard_path,
                    source,
                    {"test_required_guard"},
                )

    def test_runtime_guard_probe_refuses_method_level_skip(self):
        require_verifier_features(self, "runtime_unittest_methods")
        guard_path = verifier.INOCULATION_GUARD_PATH
        source = textwrap.dedent("""
            import unittest

            class Guard(unittest.TestCase):
                def test_required_guard(self):
                    self.skipTest("disabled real guard")
        """).encode("utf-8")
        with tempfile.TemporaryDirectory(
            prefix="inoculation-runtime-method-skip-"
        ) as raw:
            root = Path(raw)
            target = root / guard_path
            target.parent.mkdir(parents=True)
            target.write_bytes(source)
            with self.assertRaisesRegex(
                verifier.InoculationError,
                "execution probe was not complete",
            ):
                verifier.runtime_unittest_methods(
                    root,
                    guard_path,
                    source,
                    {"test_required_guard"},
                )

    def test_runtime_guard_probe_refuses_replaced_test_method_lookup(self):
        require_verifier_features(self, "runtime_unittest_methods")
        guard_path = verifier.INOCULATION_GUARD_PATH
        source = textwrap.dedent("""
            import unittest

            class Guard(unittest.TestCase):
                def __getattribute__(self, name):
                    if name == "test_required_guard":
                        return lambda: None
                    return super().__getattribute__(name)

                def test_required_guard(self):
                    raise AssertionError("red sentinel")
        """).encode("utf-8")
        with tempfile.TemporaryDirectory(
            prefix="inoculation-runtime-method-lookup-"
        ) as raw:
            root = Path(raw)
            target = root / guard_path
            target.parent.mkdir(parents=True)
            target.write_bytes(source)
            with self.assertRaisesRegex(
                verifier.InoculationError,
                "execution probe was not complete",
            ):
                verifier.runtime_unittest_methods(
                    root,
                    guard_path,
                    source,
                    {"test_required_guard"},
                )

    def test_guard_ast_refuses_control_flow_discovery_hooks(self):
        def methods(source):
            return verifier.unittest_methods(
                ast.parse(textwrap.dedent(source))
            )

        hostile = {
            "match-load-tests": (
                "dynamic unittest discovery hook",
                """
                import unittest
                class Guard(unittest.TestCase):
                    def test_guard(self): pass
                match 1:
                    case 1:
                        def load_tests(loader, standard, pattern):
                            return unittest.TestSuite()
                """,
            ),
            "try-star-load-tests": (
                "dynamic unittest discovery hook",
                """
                import unittest
                class Guard(unittest.TestCase):
                    def test_guard(self): pass
                try:
                    raise ExceptionGroup('hook', [Exception('hook')])
                except* Exception:
                    def load_tests(loader, standard, pattern):
                        return unittest.TestSuite()
                """,
            ),
            "named-expression-load-tests": (
                "dynamic unittest discovery hook",
                """
                import unittest
                class Guard(unittest.TestCase):
                    def test_guard(self): pass
                if (load_tests := lambda loader, standard, pattern: unittest.TestSuite()):
                    pass
                """,
            ),
            "default-expression-load-tests": (
                "dynamic unittest discovery hook",
                """
                import unittest
                class Guard(unittest.TestCase):
                    def test_guard(self): pass
                def helper(load=(load_tests := lambda loader, standard, pattern: unittest.TestSuite())):
                    pass
                """,
            ),
            "attribute-test-erasure": (
                "dynamic module mutation",
                """
                import unittest
                class Guard(unittest.TestCase):
                    def test_guard(self): pass
                Guard.test_guard = None
                """,
            ),
            "setattr-test-erasure": (
                "dynamic module mutation",
                """
                import unittest
                class Guard(unittest.TestCase):
                    def test_guard(self): pass
                setattr(Guard, 'test_guard', None)
                """,
            ),
        }
        for label, (message, source) in hostile.items():
            with self.subTest(case=label), self.assertRaisesRegex(
                verifier.InoculationError,
                message,
            ):
                methods(source)

    def test_guard_ast_refuses_class_namespace_mutation(self):
        require_verifier_features(self, "unittest_methods")

        class RuntimeDecoy(unittest.TestCase):
            def test_required_guard(self):
                pass

            locals().update(test_required_guard=None)

        self.assertEqual(
            0,
            unittest.defaultTestLoader.loadTestsFromTestCase(
                RuntimeDecoy
            ).countTestCases(),
        )
        source = ast.parse(textwrap.dedent("""
            import unittest

            class Guard(unittest.TestCase):
                def test_required_guard(self): pass
                locals().update(test_required_guard=None)
        """))
        with self.assertRaisesRegex(
            verifier.InoculationError,
            "dynamic TestCase namespace mutation",
        ):
            verifier.unittest_methods(source)

    def test_guard_ast_refuses_runtime_namespace_hooks(self):
        require_verifier_features(self, "unittest_methods")

        hostile = {
            "init-subclass": """
                import unittest

                class Parent(unittest.TestCase):
                    def __init_subclass__(cls):
                        del cls.test_required_guard

                class Guard(Parent):
                    def test_required_guard(self): pass
            """,
            "descriptor": """
                import unittest

                class Eraser:
                    def __set_name__(self, owner, name):
                        del owner.test_required_guard

                class Guard(unittest.TestCase):
                    def test_required_guard(self): pass
                    eraser = Eraser()
            """,
            "qualified-setattr": """
                import builtins
                import unittest

                class Guard(unittest.TestCase):
                    def test_required_guard(self): pass

                builtins.setattr(Guard, "__unittest_skip__", True)
            """,
        }
        for label, source in hostile.items():
            with self.subTest(case=label), self.assertRaisesRegex(
                verifier.InoculationError, "dynamic .* mutation"
            ):
                verifier.unittest_methods(
                    ast.parse(textwrap.dedent(source))
                )

    def test_guard_ast_refuses_direct_dunder_namespace_mutation(self):
        require_verifier_features(
            self,
            "runtime_unittest_methods",
            "unittest_methods",
        )
        source = textwrap.dedent("""
            import unittest

            class Guard(unittest.TestCase):
                def test_required_guard(self): pass

            object.__setattr__(
                Guard.__dict__["test_required_guard"],
                "__unittest_skip__",
                True,
            )
        """)
        with self.assertRaisesRegex(
            verifier.InoculationError, "dynamic module mutation"
        ):
            verifier.unittest_methods(ast.parse(source))

        alias_source = textwrap.dedent("""
            from builtins import setattr as mutate
            import unittest

            class Guard(unittest.TestCase):
                def test_required_guard(self): pass

            mutate(
                Guard.__dict__["test_required_guard"],
                "__unittest_skip__",
                True,
            )
        """).encode("utf-8")
        with tempfile.TemporaryDirectory(
            prefix="inoculation-runtime-dunder-mutation-"
        ) as raw:
            root = Path(raw)
            with self.assertRaisesRegex(
                verifier.InoculationError,
                "execution probe was not complete",
            ):
                verifier.runtime_unittest_methods(
                    root,
                    verifier.INOCULATION_GUARD_PATH,
                    alias_source,
                    {"test_required_guard"},
                )

    def test_guard_ast_refuses_implicit_discovery_and_descriptor_hooks(self):
        require_verifier_features(self, "unittest_methods")
        hostile = {
            "module-dir": """
                import unittest

                class Guard(unittest.TestCase):
                    def test_required_guard(self): pass

                def __dir__():
                    return []
            """,
            "helper-decorator": """
                import unittest

                class Eraser:
                    def __set_name__(self, owner, name):
                        del owner.test_required_guard

                def erase(function):
                    return Eraser()

                class Guard(unittest.TestCase):
                    def test_required_guard(self): pass

                    @erase
                    def helper(self): pass
            """,
        }
        for label, source in hostile.items():
            with self.subTest(case=label), self.assertRaisesRegex(
                verifier.InoculationError,
                "dynamic .* (hook|mutation)",
            ):
                verifier.unittest_methods(ast.parse(textwrap.dedent(source)))

    def test_guard_ast_refuses_module_namespace_update(self):
        require_verifier_features(self, "unittest_methods")
        source = textwrap.dedent("""
            import unittest

            class Guard(unittest.TestCase):
                def test_required_guard(self): pass

            globals().update({"Guard": object})
        """)
        class RuntimeGuard(unittest.TestCase):
            def test_required_guard(self):
                pass

        module = type(unittest)("_guard_namespace_update")
        module.__dict__.update({"Guard": RuntimeGuard})
        module.__dict__.update({"Guard": object})
        self.assertEqual(
            0,
            unittest.defaultTestLoader.loadTestsFromModule(
                module
            ).countTestCases(),
        )
        with self.assertRaisesRegex(
            verifier.InoculationError, "dynamic module mutation"
        ):
            verifier.unittest_methods(ast.parse(source))

    def test_guard_ast_refuses_import_time_helper_mutation(self):
        require_verifier_features(self, "unittest_methods")
        source = textwrap.dedent("""
            import unittest

            class Guard(unittest.TestCase):
                def test_required_guard(self): pass

            def replace_guard():
                global Guard
                class Empty(unittest.TestCase):
                    pass
                Guard = Empty

            replace_guard()
        """)
        with self.assertRaisesRegex(
            verifier.InoculationError, "dynamic module mutation"
        ):
            verifier.unittest_methods(ast.parse(source))


if __name__ == "__main__":
    unittest.main()
