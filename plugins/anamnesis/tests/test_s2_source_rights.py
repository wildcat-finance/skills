"""Rights decisions travel as a digest and remain part of release identity."""
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/anamnesis/scripts/anamnesis.py"
spec = importlib.util.spec_from_file_location("source_rights", SCRIPT)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


class SourceRights(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "specimens/estate", self.root / "specimen")
        self.specimen = self.root / "specimen"
        self.path = self.specimen / "policy.json"
        self.input = json.loads(self.path.read_bytes())
        self.policy = json.loads((self.specimen / "curation-policy.json").read_bytes())
        self.graph = {k: json.loads((self.specimen / "release" / (k + ".json")).read_bytes())
                      for k in ("engagements", "assertions", "relations", "quarantine", "unknowns")}

    @contextmanager
    def refusal(self):
        try:
            yield
        except Exception as error:
            self.assertIsInstance(error, a.Refusal, f"unnamed failure: {type(error).__name__}")
        else:
            self.fail("malformed rights were accepted")

    def admit(self):
        self.path.write_bytes(canonical(self.input))
        return a.admit(str(self.path), a.Events())["sources"]

    def test_admission_retains_canonical_full_rights_digest(self):
        admitted = self.admit()
        for source, row in zip(self.input["sources"], admitted):
            self.assertEqual(row.get("rights_sha256"), hashlib.sha256(canonical(source["rights"])).hexdigest())
            self.assertEqual(row["basis"], source["rights"]["basis"])

    def test_each_decision_field_changes_identity_even_with_graph_fixed(self):
        original = copy.deepcopy(self.input)
        baseline = a.release_id(self.policy, self.admit(), self.graph)
        for field, value in (("basis", "contract"), ("holder", "Distinct holder"),
                             ("statement", "Distinct decision"), ("disclosure", "restricted")):
            with self.subTest(field=field):
                self.input = copy.deepcopy(original)
                self.input["sources"][0]["rights"][field] = value
                self.assertNotEqual(a.release_id(self.policy, self.admit(), self.graph), baseline)

    def test_every_identity_field_tamper_is_refused(self):
        admitted = self.admit()
        out = self.root / "release"
        manifest = a.build_release(str(out), self.policy, admitted, self.graph)
        for field, value in (("id", "different"), ("sha256", "0" * 64), ("bytes", 7),
                             ("basis", "contract"), ("disclosure", "restricted"),
                             ("rights_sha256", "0" * 64)):
            with self.subTest(field=field):
                changed = copy.deepcopy(manifest)
                changed["sources"][0][field] = value
                (out / "manifest.json").write_bytes(canonical(changed))
                with self.refusal():
                    a.verify_release(str(out))

    def test_build_and_reader_refuse_invalid_rights_rows(self):
        admitted = self.admit()
        manifest = a.build_release(str(self.root / "valid"), self.policy, admitted, self.graph)
        cases = [(field, value) for field in ("basis", "disclosure", "rights_sha256")
                 for value in (None, [], {}, 7, True, "", "unknown")]
        cases += [("rights_sha256", "G" * 64), ("rights_sha256", "A" * 64),
                  ("rights_sha256", "0" * 63), ("disclosure", "embargoed"),
                  ("basis", "digest-only")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                rows = copy.deepcopy(admitted)
                rows[0][field] = value
                with self.refusal():
                    a.build_release(str(self.root / "invalid"), self.policy, rows, self.graph)
                self.assertFalse((self.root / "invalid").exists())
                changed = copy.deepcopy(manifest)
                changed["sources"][0][field] = value
                with self.refusal():
                    a.check_manifest_shape(changed)
        for field in ("basis", "disclosure", "rights_sha256"):
            with self.subTest(missing=field):
                rows = copy.deepcopy(admitted)
                rows[0].pop(field, None)
                with self.refusal():
                    a.build_release(str(self.root / "missing"), self.policy, rows, self.graph)
                changed = copy.deepcopy(manifest)
                changed["sources"][0].pop(field, None)
                with self.refusal():
                    a.check_manifest_shape(changed)

    def test_independent_preimage_and_private_text_absence(self):
        self.input["sources"][0]["rights"].update(holder="Private holder sentinel", statement="Private statement sentinel")
        admitted = self.admit()
        out = self.root / "release"
        manifest = a.build_release(str(out), self.policy, admitted, self.graph)
        digest = hashlib.sha256(canonical(self.policy))
        for row in sorted(manifest["sources"], key=lambda row: row["id"]):
            self.assertIn("rights_sha256", row)
            digest.update(":".join(str(row[k]) for k in ("id", "sha256", "bytes", "disclosure", "basis", "rights_sha256")).encode())
        for key in ("engagements", "assertions", "relations", "quarantine", "unknowns"):
            digest.update(canonical(self.graph[key]))
        self.assertEqual(manifest["release_id"], digest.hexdigest())
        payload = b"".join(p.read_bytes() for p in out.iterdir())
        self.assertNotIn(b"Private holder sentinel", payload)
        self.assertNotIn(b"Private statement sentinel", payload)

    def test_restricted_decision_stays_withheld_and_counted(self):
        self.input["sources"][0]["rights"].update(
            disclosure="restricted", basis="digest-only",
            holder="Private holder sentinel", statement="Private statement sentinel")
        self.admit()
        out = self.root / "restricted"
        manifest = a._rebuild_once(str(self.specimen), str(out))
        analogue = a.analogues(str(out), "severity", "high")
        observation = a.observations(str(out), "every public finding in the release")
        restricted = self.input["sources"][0]["id"]
        self.assertTrue(manifest["sources"])
        self.assertGreater(observation["denominators"]["findings_withheld_by_disclosure"], 0)
        self.assertNotIn(restricted, [item["source"] for item in analogue["analogues"]])
        payload = b"".join(p.read_bytes() for p in out.iterdir()) + canonical(analogue) + canonical(observation)
        self.assertNotIn(b"Private holder sentinel", payload)
        self.assertNotIn(b"Private statement sentinel", payload)

    def test_optional_rights_fields_are_part_of_the_full_decision_digest(self):
        before = self.admit()[0]
        self.input["sources"][0]["rights"]["expires"] = "2099-01-01"
        after = self.admit()[0]
        self.assertNotEqual(before.get("rights_sha256"), after.get("rights_sha256"))



class HistoricalRunIsolation(unittest.TestCase):
    def test_foreign_controller_cannot_replace_archived_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            foreign = Path(directory) / "study.md"
            foreign.write_text("another issue's study")
            for filename, method in (
                ("test_s11_registry.py", "test_the_committed_documents_equal_the_run_artefacts"),
                ("test_s14_ledger.py", "test_the_committed_documents_equal_the_receipted_artefacts"),
            ):
                spec = importlib.util.spec_from_file_location("historical_guard", ROOT / "tests" / filename)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                case = next(value for value in vars(module).values()
                            if isinstance(value, type) and issubclass(value, unittest.TestCase)
                            and hasattr(value, method))
                with mock.patch.object(module, "RUN_STUDY", foreign, create=True), \
                        mock.patch.object(module, "RUN_RUNBOOK", foreign, create=True):
                    result = unittest.TestResult()
                    case(method).run(result)
                    self.assertEqual(result.errors, [])
                    self.assertEqual(result.failures, [])
                # The archived document is still checked when a foreign run exists.
                with mock.patch.object(module, "STUDY", foreign):
                    result = unittest.TestResult()
                    case(method).run(result)
                    self.assertFalse(result.wasSuccessful())


if __name__ == "__main__":
    unittest.main()
