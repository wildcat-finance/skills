"""Released components, the consumer lock, the bounded command line and the offline demonstration.

Every refusal below is a retained counterexample: the exact released tree, the
one change made to it, and the code the release must answer with.
"""
from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/fiat/scripts"))
import checkpoint_authority_release_corpus as corpus
from checkpoint_authority import demo, native_io, network, release, signatures, verifier, wire
from checkpoint_authority.canonical import Refusal, canonical, decode, digest
from checkpoint_authority.signatures import ToolPin
from test_checkpoint_authority_records import tool, tools as pinned_tools

ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority.py"
PACKAGE = ROOT / "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority"
DEMONSTRATED = None
"""Set by the demonstration case; the suite runner reports it as evidence."""


def tools_bytes():
    return canonical({"schema": "checkpoint-authority-tools/v1",
                      "tools": {name: {"path": pin.path, "sha256": pin.sha256}
                                for name, pin in pinned_tools().items()}},
                     limit=verifier.LIMITS["tools_file_bytes"])


def cosign_pin():
    pin = tool("cosign")
    return ToolPin("cosign", pin.path, pin.sha256)


def temporary_root():
    """A resolved directory; the bounded reader refuses a symlinked path component."""
    directory = tempfile.TemporaryDirectory(prefix="checkpoint-release-")
    return directory, Path(directory.name).resolve()


class ReleaseInventoryTests(unittest.TestCase):
    def test_release_digests_rebuild_twice_identically_from_the_same_tree(self):
        first, second = release.build(ROOT), release.build(ROOT)
        self.assertEqual(release.encode(first), release.encode(second))
        self.assertEqual(release.encode(first), release.committed(ROOT)[0])

    def test_the_committed_corpus_manifest_and_lock_example_have_no_drift(self):
        for path, data in corpus.recomputed().items():
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes(), data)

    def test_the_manifest_never_hashes_itself_and_names_its_external_pins(self):
        manifest = release.check(ROOT)
        listed = {row["path"] for value in manifest["components"].values() for row in value["files"]}
        listed |= {row["path"] for row in manifest["transitive_files"]}
        self.assertNotIn(release.MANIFEST, listed)
        self.assertEqual(manifest["external_pins"], ["source_commit", "release_manifest_sha256"])
        self.assertNotIn(digest(release.committed(ROOT)[0]), release.committed(ROOT)[0].decode())

    def test_the_verifier_component_lists_every_released_module_and_the_command_line(self):
        modules = sorted(path.stem for path in PACKAGE.glob("*.py"))
        self.assertEqual(modules, sorted(release.MODULES))
        self.assertEqual(release.COMPONENTS["verifier"][-1],
                         "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority.py")

    def test_the_release_separates_authority_and_native_toolchain_pins(self):
        manifest = release.check(ROOT)
        self.assertNotEqual(manifest["native"]["source_commit"], release.PLACEHOLDER_COMMIT)
        self.assertEqual(set(manifest["native"]),
                         {"source_commit", "executable_sha256", "profile", "profile_sha256"})
        self.assertEqual(set(manifest["tools"]), {"cosign", "python"})
        self.assertNotIn("source_commit", manifest["tools"])


class ReleasedTreeRefusalTests(unittest.TestCase):
    """Each case copies the released tree, makes one change, and names the refusal."""

    def setUp(self):
        self.directory, self.copy = temporary_root()
        self.addCleanup(self.directory.cleanup)
        for prefix in ("plugins/hexaemeron/skills/fiat", "docs/checkpoint-authority", ".python-version"):
            source = ROOT / prefix
            target = self.copy / prefix
            if source.is_dir():
                shutil.copytree(source, target, symlinks=False,
                                ignore=shutil.ignore_patterns("__pycache__"))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        for row in release.check(ROOT)["transitive_files"]:
            target = self.copy / row["path"]
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / row["path"], target)

    def refuses(self, code):
        with self.assertRaises(Refusal) as caught:
            release.check(self.copy)
        self.assertEqual(caught.exception.code, code)

    def test_a_clean_copy_of_the_released_tree_still_agrees(self):
        self.assertEqual(release.encode(release.check(self.copy)),
                         release.committed(self.copy)[0])

    def test_an_altered_component_refuses_as_drift(self):
        target = self.copy / release.COMPONENTS["schemas"][0]
        target.write_bytes(target.read_bytes().replace(b"checkpoint", b"checkpoinT", 1))
        self.refuses("component-drift")

    def test_a_missing_component_refuses_as_missing(self):
        (self.copy / release.COMPONENTS["capabilities"][0]).unlink()
        self.refuses("component-missing")

    def test_an_extra_enumerated_component_refuses(self):
        (self.copy / release.CORPUS / "schemas" / "extra.schema.json").write_bytes(b"{}\n")
        self.refuses("component-extra")

    def test_a_stale_manifest_refuses_even_with_every_component_present(self):
        target = self.copy / release.MANIFEST
        value = json.loads(target.read_bytes())
        value["note"] = value["note"] + " Restated."
        target.write_bytes(release.encode(value))
        self.refuses("manifest-stale")

    def test_a_special_file_component_refuses_without_reading_it(self):
        target = self.copy / release.COMPONENTS["tools"][0]
        target.unlink()
        os.mkfifo(target)
        self.refuses("component-unsafe")

    def test_a_symlinked_component_refuses_without_following_it(self):
        target = self.copy / release.COMPONENTS["native"][0]
        payload = target.read_bytes()
        elsewhere = self.copy / "native-profile-copy.json"
        elsewhere.write_bytes(payload)
        target.unlink()
        target.symlink_to(elsewhere)
        self.refuses("component-missing")

    def test_transitive_paths_refuse_before_opening_any_component(self):
        target = self.copy / release.MANIFEST
        original = target.read_bytes()
        sentinel = self.copy.parent / (self.copy.name + "-sentinel")
        sentinel.write_bytes(b"outside the selected release\n")
        self.addCleanup(sentinel.unlink)
        for path in (str(sentinel), "../" + sentinel.name, "a/../../outside",
                     "a/./b", "a//b", "a\\b", "a\x00b"):
            value = json.loads(original)
            value["transitive_files"].append({"path": path, "sha256": digest(sentinel.read_bytes())})
            target.write_bytes(release.encode(value))
            opened = []
            reader = native_io.regular

            def observe(name, maximum):
                opened.append(Path(name))
                return reader(name, maximum)

            with self.subTest(path=path), mock.patch.object(native_io, "regular", observe):
                self.refuses("component-path")
                self.assertEqual(opened, [target])

        target.write_bytes(original)
        corpus_path = self.copy / release.CORPUS_MANIFESTS[0]
        value = json.loads(corpus_path.read_bytes())
        value["files"].append({"path": str(sentinel), "sha256": digest(sentinel.read_bytes())})
        corpus_path.write_bytes(canonical(value, limit=release.MANIFEST_MAX))
        with self.assertRaises(Refusal) as raised:
            release.build(self.copy)
        self.assertEqual(raised.exception.code, "component-path")

    def test_malformed_transitive_rows_refuse_before_opening_any_component(self):
        target = self.copy / release.MANIFEST
        original = json.loads(target.read_bytes())
        row = original["transitive_files"][0]
        for rows in (None, {}, [], [None], [{**row, "path": []}],
                     [{**row, "sha256": False}], [row, row],
                     original["transitive_files"][::-1], [row] * 1025):
            value = {**original, "transitive_files": rows}
            target.write_bytes(release.encode(value))
            with self.subTest(rows_type=type(rows).__name__), \
                    mock.patch.object(release, "_hash", side_effect=AssertionError("component opened")):
                self.refuses("manifest-shape")


class ConsumerLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock_bytes = (ROOT / release.LOCK_EXAMPLE).read_bytes()
        cls.lock = decode(cls.lock_bytes, limit=release.LOCK_MAX)

    def test_the_example_lock_agrees_with_the_committed_release(self):
        result = release.lock_check(self.lock_bytes, ROOT,
                                    source_commit=self.lock["authority"]["source_commit"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["code"], "lock-agrees")
        self.assertEqual(result["release_manifest_sha256"], digest(release.committed(ROOT)[0]))

    def test_the_example_lock_leaves_the_authority_commit_for_the_consumer(self):
        self.assertEqual(self.lock["authority"]["source_commit"], release.PLACEHOLDER_COMMIT)
        self.assertNotEqual(self.lock["native"]["source_commit"], release.PLACEHOLDER_COMMIT)

    def test_every_declared_hostile_release_case_refuses_by_its_recorded_code(self):
        declared = json.loads((ROOT / demo.HOSTILE).read_bytes())["cases"]
        rows = demo.hostile(ROOT, self.lock_bytes)
        self.assertEqual([row["id"] for row in rows], [case["id"] for case in declared])
        self.assertTrue(all(row["refused"] for row in rows))
        self.assertEqual([row["code"] for row in rows], [case["code"] for case in declared])

    def test_a_mutable_branch_or_tag_is_never_a_compatibility_decision(self):
        for reference in ("main", "latest", "HEAD", "v1", "refs/heads/main"):
            with self.subTest(reference=reference):
                mutated = json.loads(json.dumps(self.lock))
                mutated["authority"]["source_commit"] = reference
                with self.assertRaises(Refusal) as caught:
                    release.lock_check(canonical(mutated, limit=release.LOCK_MAX), ROOT)
                self.assertEqual(caught.exception.code, "mutable-source-reference")

    def test_an_asserted_commit_that_disagrees_with_the_lock_refuses(self):
        with self.assertRaises(Refusal) as caught:
            release.lock_check(self.lock_bytes, ROOT, source_commit="a" * 40)
        self.assertEqual(caught.exception.code, "source-commit-mismatch")

    def test_the_lock_check_never_runs_git_to_answer_for_the_commit(self):
        with mock.patch.object(subprocess, "Popen", side_effect=AssertionError("subprocess")), \
                mock.patch.object(subprocess, "run", side_effect=AssertionError("subprocess")):
            result = release.lock_check(self.lock_bytes, ROOT)
        self.assertFalse(result["source_commit_asserted"])


class CommandLineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory, cls.scratch = temporary_root()
        cls.tools = cls.scratch / "tools.json"
        cls.tools.write_bytes(tools_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def cli(self, *argv, cwd=None):
        result = subprocess.run([sys.executable, str(CLI), *argv], capture_output=True,
                                cwd=str(cwd or ROOT), timeout=900,
                                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C",
                                     "PYTHONDONTWRITEBYTECODE": "1"})
        return result.returncode, json.loads(result.stdout) if result.stdout else None

    def test_the_release_operation_reports_the_agreeing_components(self):
        code, event = self.cli("release")
        self.assertEqual(code, 0, event)
        self.assertEqual(event["code"], "components-agree")
        self.assertEqual(event["release_manifest_sha256"], digest(release.committed(ROOT)[0]))
        self.assertGreaterEqual(event["files"], len(release.COMPONENTS["schemas"]))

    def test_the_lock_operation_reports_the_verified_pins(self):
        code, event = self.cli("lock", "--lock", str(ROOT / release.LOCK_EXAMPLE),
                               "--source-commit", release.PLACEHOLDER_COMMIT)
        self.assertEqual(code, 0, event)
        self.assertEqual(event["code"], "lock-agrees")
        self.assertTrue(event["source_commit_asserted"])

    def test_the_verify_operation_reconstructs_the_history_from_named_files_alone(self):
        code, event = self.cli("verify", "--history", str(ROOT / demo.HISTORY),
                               "--bootstrap", str(ROOT / demo.BOOTSTRAP),
                               "--tools", str(self.tools), "--native", str(ROOT / demo.NATIVE),
                               "--freshness", str(ROOT / demo.FRESHNESS),
                               "--presence", str(ROOT / demo.PRESENCE))
        expected = json.loads((ROOT / demo.EXPECTED).read_bytes())
        self.assertEqual(code, 0, event)
        self.assertTrue(event["complete"])
        self.assertEqual(event["historical"], "valid")
        self.assertEqual(event["history_sha256"], expected["history_sha256"])
        self.assertEqual(event["eligibility_summary"]["eligible"], expected["eligible"])

    def test_an_unknown_operation_or_operand_exits_two_without_echoing_it(self):
        for argv in (("publish",), ("release", "--fetch", "https://example.invalid"),
                     ("verify",), ("lock",), ()):
            with self.subTest(argv=argv):
                code, event = self.cli(*argv)
                self.assertEqual(code, 2)
                self.assertEqual(event["code"], "invalid-invocation")
                self.assertNotIn("example.invalid", json.dumps(event))

    def test_a_symlinked_or_special_input_refuses(self):
        linked = self.scratch / "linked-tools.json"
        if not linked.is_symlink():
            linked.symlink_to(self.tools)
        fifo = self.scratch / "fifo-tools.json"
        if not fifo.exists():
            os.mkfifo(fifo)
        for operand in (linked, fifo):
            with self.subTest(operand=operand.name):
                code, event = self.cli("demonstrate", "--tools", str(operand))
                self.assertEqual(code, 1)
                self.assertFalse(event["complete"])

    def test_a_report_path_is_created_exclusively_and_never_replaced(self):
        target = self.scratch / "report.json"
        code, _ = self.cli("release", "--out", str(target))
        self.assertEqual(code, 0)
        first = target.read_bytes()
        code, event = self.cli("release", "--out", str(target))
        self.assertEqual(code, 1)
        self.assertEqual(event["code"], "report-exists")
        self.assertEqual(target.read_bytes(), first)

    def test_no_file_outside_the_named_operands_is_opened_by_the_bounded_reader(self):
        opened = []
        original = native_io.regular

        def observe(path, maximum):
            opened.append(Path(path).resolve())
            return original(path, maximum)

        with mock.patch.object(native_io, "regular", observe):
            verifier.verify(verifier.History(ROOT / demo.HISTORY),
                            verifier.bootstrap_from((ROOT / demo.BOOTSTRAP).read_bytes()),
                            pinned_tools(),
                            native=verifier.native_from((ROOT / demo.NATIVE).read_bytes()),
                            freshness=verifier.freshness_from((ROOT / demo.FRESHNESS).read_bytes()),
                            presence=verifier.presence_from((ROOT / demo.PRESENCE).read_bytes()))
        self.assertEqual(opened, [(ROOT / demo.HISTORY).resolve()])

    def test_no_released_module_imports_a_network_or_url_interface(self):
        forbidden = ("urllib", "http.client", "httplib", "socket", "ssl", "ftplib",
                     "requests", "asyncio", "smtplib", "webbrowser", "xmlrpc")
        for path in (*PACKAGE.glob("*.py"), CLI):
            text = path.read_text(encoding="utf-8")
            for name in forbidden:
                with self.subTest(module=path.name, forbidden=name):
                    self.assertNotIn("import " + name, text)


class _SpawnShim:
    """Stand in for the `subprocess` name inside `signatures` for one case only."""

    PIPE = subprocess.PIPE
    TimeoutExpired = subprocess.TimeoutExpired
    SubprocessError = subprocess.SubprocessError

    def __init__(self, failures, code):
        self.failures, self.code, self.attempts = failures, code, 0

    def Popen(self, *args, **kwargs):
        self.attempts += 1
        if self.failures:
            self.failures -= 1
            raise OSError(self.code, "injected transient spawn failure")
        return subprocess.Popen(*args, **kwargs)


class TransientToolSpawnTests(unittest.TestCase):
    """A host that cannot start a child right now is not an unavailable tool.

    Observed on 2026-09-19 on the released tree: eight concurrent copies of
    this module refused three times with `tool-unavailable` raised by
    `openssl dgst`, in the released demonstration and in the Step 4 replay
    suite alike, while the host was under process pressure. Without the
    bounded spawn retry in `signatures._spawn` the first case below refuses.
    """

    def setUp(self):
        self.directory, self.scratch = temporary_root()
        self.addCleanup(self.directory.cleanup)

    def spawn(self, failures, code=errno.EAGAIN, timeout=5):
        shim = _SpawnShim(failures, code)
        pin = pinned_tools()["openssl"]
        with mock.patch.object(signatures, "subprocess", shim):
            try:
                return shim, signatures._run(pin, ["version"], self.scratch, timeout=timeout)
            except Refusal as error:
                return shim, error

    def test_a_transient_spawn_failure_is_retried_rather_than_reported_unavailable(self):
        shim, result = self.spawn(3)
        self.assertNotIsInstance(result, Refusal)
        self.assertEqual(result[0], 0)
        self.assertIn(b"OpenSSL", result[1])
        self.assertEqual(shim.attempts, 4)

    def test_a_spawn_failure_that_persists_to_the_deadline_still_refuses(self):
        shim, result = self.spawn(10 ** 6, timeout=0.2)
        self.assertIsInstance(result, Refusal)
        self.assertEqual(result.code, "tool-unavailable")
        self.assertEqual(result.stage, "signature")
        self.assertGreater(shim.attempts, 1)

    def test_a_spawn_error_outside_the_transient_set_is_never_retried(self):
        shim, result = self.spawn(1, code=errno.ENOENT)
        self.assertIsInstance(result, Refusal)
        self.assertEqual(result.code, "tool-unavailable")
        self.assertEqual(shim.attempts, 1)

    def test_only_host_exhaustion_errnos_are_treated_as_transient(self):
        self.assertEqual(signatures.TRANSIENT_SPAWN,
                         frozenset((errno.EAGAIN, errno.ENOMEM, errno.EMFILE,
                                    errno.ENFILE, errno.EINTR)))
        self.assertNotIn(errno.ENOENT, signatures.TRANSIENT_SPAWN)
        self.assertNotIn(errno.EACCES, signatures.TRANSIENT_SPAWN)


class NetworkDenialTests(unittest.TestCase):
    def test_the_demonstration_blocks_a_verifier_that_attempts_a_real_socket(self):
        directory, scratch = temporary_root(); self.addCleanup(directory.cleanup)
        marker = scratch / "network-created"
        valid = json.loads((ROOT / demo.COSIGN_ENVELOPE).read_bytes())
        source = "#!" + sys.executable + "\n" + """import errno, json, pathlib, socket, sys
marker = pathlib.Path(%r)
try:
    with socket.socket() as connection:
        connection.bind(('127.0.0.1', 0))
except OSError as error:
    if error.errno not in (errno.EPERM, errno.EACCES):
        raise
else:
    marker.write_text('network creation succeeded')
bundle = json.loads(pathlib.Path('bundle.json').read_bytes())
valid = %r
key = sys.argv[sys.argv.index('--key') + 1]
sys.exit(0 if bundle['dsseEnvelope'] == valid and key == 'trusted.pem' else 1)
""" % (str(marker), valid)
        executable = scratch / "cosign-probe"; executable.write_text(source); executable.chmod(0o700)
        pin = ToolPin("cosign", str(executable), digest(executable.read_bytes()))
        self.assertTrue(demo.interoperability(ROOT, pin)["agreed"])
        self.assertFalse(marker.exists(), "the alleged denied-network verifier created a socket")

    def test_an_unsupported_host_refuses_to_claim_network_denial(self):
        with mock.patch.object(network.sys, "platform", "unsupported"), self.assertRaises(Refusal) as raised:
            network.prepare()
        self.assertEqual(raised.exception.code, "network-denial-unavailable")

    def test_a_failed_or_incomplete_network_probe_refuses(self):
        directory, scratch = temporary_root(); self.addCleanup(directory.cleanup)
        boundary = network.prepare()
        for value in ((1, network.PROBE_OUTPUT, b""), (0, b"", b""),
                      (0, network.PROBE_OUTPUT[:-1], b"")):
            with self.subTest(exit=value[0]), mock.patch.object(network.Boundary, "run", return_value=value), \
                    self.assertRaises(Refusal) as raised:
                boundary.probe(scratch)
            self.assertEqual(raised.exception.code, "network-denial-probe")

    def test_a_changed_network_launcher_refuses(self):
        directory, scratch = temporary_root(); self.addCleanup(directory.cleanup)
        boundary = network.Boundary("0" * 64)
        with self.assertRaises(Refusal) as raised:
            boundary.run(pinned_tools()["openssl"], ["version"], scratch, timeout=5)
        self.assertEqual(raised.exception.code, "network-denial-changed")

    def test_an_absent_independent_verifier_never_claims_network_denial(self):
        self.assertEqual(demo.interoperability(ROOT, None)["network"], "not-established")


class InstalledPluginTests(unittest.TestCase):
    """The released verifier must run from an isolated copy of its own components."""

    def test_the_released_verifier_runs_outside_the_repository_checkout(self):
        directory, isolated = temporary_root()
        self.addCleanup(directory.cleanup)
        prefix = "plugins/hexaemeron/skills/fiat/scripts"
        shutil.copytree(PACKAGE, isolated / prefix / "checkpoint_authority",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(CLI, isolated / prefix / "checkpoint_authority.py")
        for relative in (demo.HISTORY, demo.BOOTSTRAP, demo.NATIVE, demo.FRESHNESS, demo.PRESENCE):
            target = isolated / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        tools = isolated / "tools.json"
        tools.write_bytes(tools_bytes())
        result = subprocess.run(
            [sys.executable, str(isolated / prefix / "checkpoint_authority.py"), "verify",
             "--history", str(isolated / demo.HISTORY),
             "--bootstrap", str(isolated / demo.BOOTSTRAP), "--tools", str(tools),
             "--native", str(isolated / demo.NATIVE),
             "--freshness", str(isolated / demo.FRESHNESS),
             "--presence", str(isolated / demo.PRESENCE)],
            capture_output=True, cwd=str(isolated), timeout=900,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"})
        event = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, event)
        self.assertTrue(event["complete"])
        self.assertEqual(event["eligibility_summary"]["eligible"],
                         json.loads((ROOT / demo.EXPECTED).read_bytes())["eligible"])


class AriadneBoundaryTests(unittest.TestCase):
    """An Ariadne pass binds evidence; it never upgrades signature or authority claims."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "plugins/ariadne/scripts"))
        from ariadne_lib.predicates import checkpoint_authority as predicate
        cls.predicate = predicate

    def test_the_predicate_declares_what_it_did_not_authenticate(self):
        unchecked = " ".join(self.predicate.UNCHECKED).lower()
        for claim in ("signatures", "issuer authority", "complete journal replay",
                      "current eligibility"):
            with self.subTest(claim=claim):
                self.assertIn(claim, unchecked)

    def test_the_predicate_never_produces_a_replay_result_value(self):
        self.assertEqual(self.predicate.RESULTS, wire.RESULTS)
        names = {name for number, name in self.predicate.EXPECTED_RESULTS}
        self.assertEqual(names, {"environment", "comparison", "predicate-fields", "subject-roles",
                                 "evidence-references", "required-coverage"})
        self.assertNotIn("signature", names)

    def test_an_ariadne_pass_alone_establishes_no_current_eligibility(self):
        statement = json.loads(
            (ROOT / "plugins/ariadne/tests/fixtures/conformance/"
                    "pass-checkpoint-authority-acceptance.json").read_bytes())
        self.assertNotIn("current_eligibility", json.dumps(statement.get("expected", {})))
        result, _ = demo.reconstruct(ROOT, {"bootstrap": verifier.bootstrap_from(
            (ROOT / demo.BOOTSTRAP).read_bytes()), "tools": pinned_tools(),
            "native": verifier.native_from((ROOT / demo.NATIVE).read_bytes()),
            "freshness": None, "presence": None}, freshness=False, presence=False)
        self.assertFalse(result["current_eligibility_established"])


class DemonstrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outcome = demo.run(ROOT, tools_bytes=tools_bytes(), cosign=cosign_pin())

    def test_the_offline_demonstration_reconstructs_the_complete_accepted_history(self):
        global DEMONSTRATED
        outcome = self.outcome
        history, release_block = outcome["history"], outcome["release"]
        self.assertTrue(outcome["complete"])
        self.assertEqual(outcome["code"], "demonstration-complete")
        self.assertEqual(history["reconstruction"], "files-only")
        self.assertFalse(history["database_consulted"])
        self.assertEqual(history["historical"], "valid")
        self.assertGreaterEqual(history["eligible"], 1)
        self.assertLess(history["measured"]["peak_rss_bytes"],
                        release.RESOURCE_LIMITS["declared_peak_rss_ceiling_bytes"])
        DEMONSTRATED = {
            "manifest_sha256": release_block["manifest_sha256"],
            "reproducible_rebuilds": release_block["reproducible_rebuilds"],
            "history_sha256": history["history_sha256"], "head_sha256": history["head_sha256"],
            "records": history["records"], "accepted": history["accepted"],
            "eligible": history["eligible"], "hostile_refused": len(outcome["hostile"]),
            "interoperability_cases": len(outcome["interoperability"]["cases"]),
            "network_boundary": outcome["interoperability"]["network_boundary"],
            "current_eligibility_withheld":
                not outcome["withheld_evidence"]["without_freshness"]["current_eligibility_established"],
            "wall_ms": history["measured"]["wall_ms"],
            "json_decodes": history["measured"]["json_decodes"],
            "tracemalloc_peak_bytes": history["measured"]["tracemalloc_peak_bytes"],
            "peak_rss_bytes": history["measured"]["peak_rss_bytes"],
        }

    def test_a_valid_history_without_fresh_evidence_invents_no_current_permission(self):
        withheld = self.outcome["withheld_evidence"]
        self.assertEqual(withheld["without_freshness"]["historical"], "valid")
        self.assertEqual(withheld["without_freshness"]["current_eligibility"], "unknown")
        self.assertFalse(withheld["without_freshness"]["current_eligibility_established"])
        self.assertEqual(withheld["without_copy_observations"]["current_eligibility"], "unavailable")

    def test_the_independent_verifier_agrees_on_every_released_case_under_network_denial(self):
        interoperability = self.outcome["interoperability"]
        self.assertTrue(interoperability["agreed"])
        self.assertEqual(interoperability["network"], "denied")
        self.assertEqual(interoperability["network_boundary"]["probe_operations"], 4)
        self.assertEqual(interoperability["network_boundary"]["probe_exit"], 0)
        self.assertEqual(interoperability["transparency_log"], "not-consulted")
        self.assertEqual([row["id"] for row in interoperability["cases"]],
                         [case[0] for case in demo.COSIGN_CASES])
        self.assertTrue(all(row["agreed"] for row in interoperability["cases"]))

    def test_the_demonstration_records_its_supported_resource_limits(self):
        limits = self.outcome["limits"]
        self.assertEqual(limits["supported_resource_limits"], release.RESOURCE_LIMITS)
        self.assertEqual(limits["history_entries"], verifier.LIMITS["history_entries"])
        self.assertIn("No production latency", self.outcome["boundary"])
