"""Public parser controls and admission of separately saved CLI observations."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
import unittest
from unittest import mock

if __package__:
    from . import support
    from . import wildcat_v3_custody as custody
    from .wildcat_v3_reports import EvidenceUnavailable, ObservedResult, result_status
    from .wildcat_v3_execution import mutate
else:
    import support
    import wildcat_v3_custody as custody
    from wildcat_v3_reports import EvidenceUnavailable, ObservedResult, result_status
    from wildcat_v3_execution import mutate


def _cli(arguments):
    """Exercise the literal public entry and its parser in this control process."""
    stdout, stderr = io.StringIO(), io.StringIO()
    with mock.patch.object(sys, "argv", [str(support.SCRIPTS / "tabularium.py"), *arguments]), \
            redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            runpy.run_path(str(support.SCRIPTS / "tabularium.py"), run_name="__main__")
        except SystemExit as result:
            return result.code, stdout.getvalue(), stderr.getvalue()
    raise AssertionError("literal CLI entry did not exit")


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _copy_writable(source, target):
    shutil.copytree(source, target)
    for path in target.rglob("*"):
        if path.is_file():
            path.chmod(0o600)


class PublicReproductionTests(unittest.TestCase):
    """Ordinary discovery uses constructed bytes without retained custody."""

    def test_literal_public_cli_rebuilds_and_verifies_disjoint_moved_releases(self):
        for venue, rows in (("wildcat-v1", 7), ("wildcat-v2", 10)):
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                public = support.EXAMPLES / (venue + "-v0") / "release"
                target, moved = base / "built", base / "moved"
                release = json.loads((public / "coverage.json").read_bytes())["release"]
                result, stdout, stderr = _cli(["wildcat-canonical", "--alexandria-release",
                                               str(public / "source/raw-release"), "--release", release,
                                               "--out", str(target)])
                self.assertEqual((result, stderr), (0, ""))
                self.assertEqual(json.loads(stdout)["rows"], rows)
                expected = custody.file_inventory(public)
                actual = custody.file_inventory(target)
                self.assertEqual(actual["files"], expected["files"])
                shutil.copytree(target, moved)
                shutil.rmtree(target)
                result, stdout, stderr = _cli(["verify", str(moved / "coverage.json")])
                self.assertEqual((result, stderr), (0, ""))
                self.assertEqual(json.loads(stdout)["rows"], rows)

    def test_rehashed_public_party_copy_reaches_specific_semantic_refusal(self):
        for venue in ("wildcat-v1", "wildcat-v2"):
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary).resolve() / "copy"
                shutil.copytree(support.EXAMPLES / (venue + "-v0") / "release", target)
                path = target / "events.jsonl"
                rows = [json.loads(line) for line in path.read_bytes().splitlines()]
                deposit = next(row for row in rows if row["action"].endswith(".deposit"))
                deposit["parties"][0]["address"] = "0x" + "99" * 20
                data = b"".join(json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n"
                                for row in rows)
                path.chmod(0o600)
                path.write_bytes(data)
                coverage = json.loads((target / "coverage.json").read_bytes())
                coverage["canonical"].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                (target / "coverage.json").chmod(0o600)
                _write(target / "coverage.json", coverage)
                result, stdout, stderr = _cli(["verify", str(target / "coverage.json")])
                self.assertEqual((result, stdout), (1, ""))
                self.assertEqual(stderr, "tabularium: verification failed: Wildcat events.jsonl differs from its offline semantic rebuild\n")

    def test_missing_saved_custody_refuses_without_starting_a_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch("subprocess.Popen", side_effect=AssertionError("unexpected process")):
                with self.assertRaises(EvidenceUnavailable):
                    custody.admit(Path(temporary).resolve())

    def test_actual_pin_selection_requires_admission_support_and_package_source(self):
        namespace = runpy.run_path(str(custody.REPO / "plugins/tabularium/tests/execute_wildcat_v3_reproduction.py"))
        pins = namespace["code_pins"](custody.REPO)
        code = {str(custody.REPO / item["path"]): item for item in pins}
        for filename in ("support.py", "__init__.py"):
            with self.subTest(filename=filename):
                path = str(custody.REPO / "plugins/tabularium/tests" / filename)
                self.assertIn(path, code)
                omitted = {key: value for key, value in code.items() if key != path}
                with self.assertRaisesRegex(EvidenceUnavailable, "code.complete-resource-set"):
                    custody._code_closure(omitted, custody.REPO)

    def test_private_inventory_rehash_cannot_replace_candidate_anchor(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as external:
            repo, root = Path(temporary).resolve(), Path(external).resolve()
            private = root / "inventory.json"
            private.write_bytes(b'{"changed":true}\n')
            _, changed = custody.read_file(private)
            locator = {"schema": "wildcat-v3-custody-locator/v1", "root": str(root),
                       "inventory": {"path": "inventory.json", **changed}}
            summary = {"schema": "wildcat-v3-reproduction-summary/v1",
                       "inventory": {"bytes": 10, "sha256": "a" * 64}, "inputs": [],
                       "operations": 52, "mutation_refusals": 20, "network_attempts": 0,
                       "limits": ["Constructed refusal specimen; no execution asserted."]}
            _write(repo / custody.LOCATOR, locator)
            _write(repo / custody.SUMMARY, summary)
            with self.assertRaisesRegex(EvidenceUnavailable, "independent-anchor"):
                custody.admit(repo)

    def test_duplicate_json_keys_refuse(self):
        for data in (b'{"schema":1,"schema":2}', b'{"nested":{"bytes":0,"bytes":1}}'):
            with self.subTest(data=data), self.assertRaises(EvidenceUnavailable):
                custody.parse_json(data)

    def test_nonfinite_json_refuses(self):
        for data in (b'{"duration":NaN}', b'{"duration":Infinity}'):
            with self.subTest(data=data), self.assertRaises(EvidenceUnavailable):
                custody.parse_json(data)

    def test_unknown_receipt_fields_and_boolean_counts_refuse(self):
        with self.assertRaises(EvidenceUnavailable):
            custody.closed({"bytes": 0, "sha256": "a" * 64, "complete": True},
                           ("bytes", "sha256"), "claim")
        for value in (True, False, -1, 1.0, "1"):
            with self.subTest(value=value), self.assertRaises(EvidenceUnavailable):
                custody.integer(value, "count")

    def test_mutation_kind_cannot_be_relabelled_by_rehashing_its_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            original, mutant = base / "original", base / "mutant"
            shutil.copytree(support.EXAMPLES / "wildcat-v1-v0/release", original)
            _copy_writable(original, mutant)
            before = custody.inventory_shape(custody.file_inventory(original))
            mutate(mutant, "selector")
            after = custody.inventory_shape(custody.file_inventory(mutant))
            changed = sorted(path for path in before if before[path] != after[path])
            custody._mutation_semantics(original, mutant, "selector", changed, before, after)
            with self.assertRaisesRegex(EvidenceUnavailable, "exact-deposit-change"):
                custody._mutation_semantics(original, mutant, "party", changed, before, after)

    def test_mutation_extra_changed_record_and_coverage_fields_refuse(self):
        for extra in ("record", "coverage"):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                original, mutant = base / "original", base / "mutant"
                shutil.copytree(support.EXAMPLES / "wildcat-v1-v0/release", original)
                _copy_writable(original, mutant)
                before = custody.inventory_shape(custody.file_inventory(original))
                mutate(mutant, "party")
                if extra == "record":
                    events = mutant / "events.jsonl"
                    rows = events.read_bytes().splitlines(keepends=True)
                    row = json.loads(rows[-1])
                    row["provenance"]["source_selector"] = "wildcat-journal:" + "a" * 64
                    rows[-1] = json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n"
                    events.write_bytes(b"".join(rows))
                    value = json.loads((mutant / "coverage.json").read_bytes())
                    _, claim = custody.read_file(events)
                    value["canonical"].update(claim)
                    _write(mutant / "coverage.json", value)
                else:
                    value = json.loads((mutant / "coverage.json").read_bytes())
                    value["known_gaps"] = []
                    _write(mutant / "coverage.json", value)
                after = custody.inventory_shape(custody.file_inventory(mutant))
                changed = sorted(path for path in before if before[path] != after[path])
                with self.assertRaises(EvidenceUnavailable):
                    custody._mutation_semantics(original, mutant, "party", changed, before, after)

    def test_mapping_class_change_preserves_every_other_descriptor_byte(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            original, mutant = base / "original", base / "mutant"
            shutil.copytree(support.EXAMPLES / "wildcat-v2-v0/release", original)
            _copy_writable(original, mutant)
            before = custody.inventory_shape(custody.file_inventory(original))
            mutate(mutant, "mapping-class")
            after = custody.inventory_shape(custody.file_inventory(mutant))
            changed = sorted(path for path in before if before[path] != after[path])
            custody._mutation_semantics(original, mutant, "mapping-class", changed, before, after)
            source = json.loads((mutant / "source.json").read_bytes())
            source["mapping_records"][1]["evidence_class"] = "inferred"
            _write(mutant / "source.json", source)
            after = custody.inventory_shape(custody.file_inventory(mutant))
            with self.assertRaises(EvidenceUnavailable):
                custody._mutation_semantics(original, mutant, "mapping-class", changed, before, after)

    def test_reference_roles_require_separate_preserved_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "stdout").write_bytes(b"same")
            _, claim = custody.read_file(root / "stdout")
            reference = {"path": "stdout", **claim}
            observer = custody.Custody(root)
            self.assertEqual(observer.ref(reference, json_value=False), b"same")
            with self.assertRaisesRegex(EvidenceUnavailable, "reference.alias"):
                observer.ref(reference, json_value=False)

    def test_saved_diagnostic_fixture_refuses_unexpected_stdout_or_stderr(self):
        for stream_name in ("stdout", "stderr"):
            with self.subTest(stream=stream_name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                def reference(name):
                    _, claim = custody.read_file(root / name)
                    return {"path": name, **claim}
                _write(root / "network.json", {"schema": "wildcat-v3-network-observation/v1",
                                                "attempts": 0, "exception": None, "cli_exit": 0})
                source = Path(__file__).resolve()
                _, pin = custody.read_file(source)
                _write(root / "modules.json", {"schema": "wildcat-v3-loaded-modules/v1",
                                                "modules": [{"name": "synthetic-control", "path": str(source), **pin}]})
                guard = "plugins/tabularium/tests/wildcat_v3_offline_cli.py"
                cli = ["diagnostic", "compatibility"]
                process = [sys.executable, "-I", "-S", "-B", "-X", "pycache_prefix=" + str(root / "absent-cache"),
                           str(custody.REPO / guard), "--repo", str(custody.REPO), "--guard-report",
                           str(root / "network.json"), "--modules-report", str(root / "modules.json"), "--", *cli]
                receipt = {"schema": "wildcat-v3-cli-observation/v1", "id": "guard-compatibility",
                           "label": "guard", "kind": "diagnostic", "process_argv": process, "cli_argv": cli,
                           "started_at_utc": "2026-10-04T00:00:00Z", "finished_at_utc": "2026-10-04T00:00:00Z",
                           "duration_seconds": 0, "exit": 0, "timed_out": False, "stdout_truncated": False,
                           "stderr_truncated": False, "exception": None, "network_attempts": 0,
                           "guard_report": reference("network.json"), "loaded_modules": reference("modules.json")}
                _write(root / "receipt.json", receipt)
                for name in ("stdout", "stderr"):
                    (root / name).write_bytes(b"unexpected" if name == stream_name else b"")
                operation = {"id": "guard-compatibility", "label": "guard", "kind": "diagnostic",
                             "receipt": reference("receipt.json"), "stdout": reference("stdout"), "stderr": reference("stderr")}
                inventory = {"runtime": {"executable": sys.executable}, "guard": {"path": guard}}
                with self.assertRaisesRegex(EvidenceUnavailable, "diagnostic.empty-streams"):
                    custody._operation(custody.Custody(root), operation, custody.REPO,
                                       inventory, {str(source): pin}, set(), diagnostic=True)

    def test_relative_path_escape_aliases_refuse(self):
        for path in ("../inventory.json", "/tmp/inventory.json", "a/../b", "a//b", "a/./b", "a\\b", "a\nb"):
            with self.subTest(path=path), self.assertRaises(EvidenceUnavailable):
                custody.relative(path, "path")

    def test_symlink_hardlink_and_fifo_files_refuse(self):
        for kind in ("symlink", "hardlink", "fifo"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                original, alias = base / "original", base / "alias"
                original.write_bytes(b"source")
                if kind == "symlink":
                    alias.symlink_to(original)
                elif kind == "hardlink":
                    os.link(original, alias)
                else:
                    os.mkfifo(alias)
                with self.assertRaises((EvidenceUnavailable, OSError)):
                    custody.read_file(alias)

    def test_parent_symlink_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            target, alias = base / "target", base / "alias"
            target.mkdir()
            (target / "receipt").write_bytes(b"source")
            alias.symlink_to(target, target_is_directory=True)
            with self.assertRaises(OSError):
                custody.read_file(alias / "receipt")

    def test_empty_stream_is_still_required_and_digest_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path = root / "stderr"
            path.write_bytes(b"")
            reference = {"path": "stderr", "bytes": 0, "sha256": hashlib.sha256(b"").hexdigest()}
            self.assertEqual(custody.Custody(root).ref(reference, json_value=False), b"")
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                custody.Custody(root).ref(reference, json_value=False)

    def test_reference_digest_conflict_and_byte_cap_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "receipt").write_bytes(b"abcdef")
            with self.assertRaisesRegex(EvidenceUnavailable, "byte-cap"):
                custody.read_file(root / "receipt", cap=5)
            with self.assertRaisesRegex(EvidenceUnavailable, "reference.digest"):
                custody.Custody(root).ref({"path": "receipt", "bytes": 6, "sha256": "a" * 64}, json_value=False)

    def test_file_identity_change_during_read_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / "receipt"
            path.write_bytes(b"before")
            with custody.StableFile(path) as reader:
                path.write_bytes(b"after")
                with self.assertRaisesRegex(EvidenceUnavailable, "read-identity"):
                    reader.check()

    def test_additional_empty_directory_and_duplicate_inventory_path_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "receipt").write_bytes(b"source")
            inventory = custody.file_inventory(root)
            inventory["files"].append(inventory["files"][0])
            with self.assertRaisesRegex(EvidenceUnavailable, "duplicate-path"):
                custody.inventory_shape(inventory)
            (root / "empty").mkdir()
            with self.assertRaisesRegex(EvidenceUnavailable, "empty-directory"):
                custody.file_inventory(root)

    def test_exact_focused_class_requires_custody_even_when_discovery_omits_it(self):
        with mock.patch.object(custody, "admit", side_effect=EvidenceUnavailable("missing saved observations")):
            result = ObservedResult()
            unittest.TestLoader().loadTestsFromTestCase(ReleaseReproductionTests).run(result)
        self.assertEqual(result.testsRun, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result_status(result), 2)


class ReleaseReproductionTests(unittest.TestCase):
    """Admit the saved four-input matrix; this focused class executes no CLI."""

    @classmethod
    def setUpClass(cls):
        cls.saved = custody.admit()

    def test_saved_input_identities_and_complete_public_summary(self):
        self.assertEqual({item["label"] for item in self.saved["inputs"]}, set(custody.INPUTS))

    def test_saved_positive_build_verify_and_moved_observations(self):
        self.assertEqual(self.saved["operations"], 52)

    def test_saved_independent_mutations_reached_specific_semantic_refusals(self):
        self.assertEqual(self.saved["mutation_refusals"], 20)

    def test_saved_operation_network_attempts_are_zero(self):
        self.assertEqual(self.saved["network_attempts"], 0)


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromTestCase(PublicReproductionTests)
