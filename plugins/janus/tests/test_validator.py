"""The manifest validator accepts the honest manifest and rejects each fault.

The honest Wildcat manifest under `harness/manifests/` must validate, and each
fixture under `fixtures/` must fail with the specific code its name carries.
The codes are an interface other tools cite, so a fixture that failed with the
wrong code would be a silent contract break; the test pins the code, not just
the failure.
"""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JANUS = ROOT / "scripts" / "janus.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
HONEST = ROOT / "harness" / "manifests" / "wildcat-open-term.json"


def load_janus():
    spec = importlib.util.spec_from_file_location("janus_cli", JANUS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.janus = load_janus()

    def test_the_honest_manifest_validates(self):
        ok, message = self.janus.validate_manifest_file(str(HONEST))
        self.assertTrue(ok, message)

    def test_each_fixture_fails_with_its_named_code(self):
        fixtures = sorted(FIXTURES.glob("j*.json"))
        self.assertGreaterEqual(len(fixtures), 18, "fixtures are missing")
        for path in fixtures:
            expected = path.name.split("_", 1)[0].upper()  # e.g. "J009"
            with self.subTest(fixture=path.name):
                ok, message = self.janus.validate_manifest_file(str(path))
                self.assertFalse(ok, f"{path.name} unexpectedly validated")
                self.assertTrue(
                    message.startswith(expected + ":"),
                    f"{path.name}: expected {expected}, got {message}",
                )

    def test_validate_command_exit_code(self):
        # A valid file exits 0; a batch containing one bad file exits 1.
        self.assertEqual(self.janus.main(["validate", str(HONEST)]), 0)
        bad = str(FIXTURES / "j009_wildcard.json")
        self.assertEqual(self.janus.main(["validate", str(HONEST), bad]), 1)

    def test_wildcard_is_rejected_everywhere_it_could_hide(self):
        # Gate 1: a wildcard in a call target or a value recipient is refused
        # just as it is in a storage slot.
        import json

        honest = json.loads(HONEST.read_text(encoding="utf-8"))
        honest.pop("$schema", None)
        for name, entry in (
            ("permittedCalls", {"target": "any", "kind": "call"}),
            ("permittedValueMovements", {"asset": "USDC", "recipient": "*"}),
        ):
            with self.subTest(field=name):
                probe = json.loads(json.dumps(honest))
                probe["thresholds"][0][name] = [entry]
                with self.assertRaises(self.janus.ManifestError) as caught:
                    self.janus.validate_manifest_obj(probe)
                self.assertEqual(caught.exception.code, "J009")


class HostSourceTests(unittest.TestCase):
    """A manifest names the host source it was written against, or says it cannot."""

    def setUp(self):
        import json

        self.janus = load_janus()
        self.honest = json.loads(HONEST.read_text(encoding="utf-8"))
        self.honest.pop("$schema", None)

    def _probe(self, source):
        import json

        probe = json.loads(json.dumps(self.honest))
        probe["hostSource"] = source
        return probe

    def test_the_shipped_manifest_binds_the_v2_5_anchor_commit(self):
        self.assertEqual(
            {
                "status": "bound",
                "repository": "https://github.com/wildcat-finance/v2-protocol",
                "revision": "9716e78e345a84fa1491c794aa5ae162790ce378",
            },
            self.honest["hostSource"],
        )

    def test_a_manifest_with_no_host_source_is_refused(self):
        del self.honest["hostSource"]
        with self.assertRaises(self.janus.ManifestError) as caught:
            self.janus.validate_manifest_obj(self.honest)
        self.assertEqual("J002", caught.exception.code)
        self.assertIn("'hostSource'", caught.exception.message)

    def test_a_declared_absence_with_its_reason_validates(self):
        self.janus.validate_manifest_obj(
            self._probe({"status": "unbound", "reason": "the host publishes no source"})
        )

    def test_each_half_filled_or_malformed_source_is_refused(self):
        repository = "https://github.com/wildcat-finance/v2-protocol"
        revision = "9716e78e345a84fa1491c794aa5ae162790ce378"
        cases = {
            "not an object": "9716e78",
            "no status": {"repository": repository, "revision": revision},
            "unknown status": {"status": "pinned", "repository": repository, "revision": revision},
            "status not a string": {"status": ["bound"], "repository": repository, "revision": revision},
            "bound without repository": {"status": "bound", "revision": revision},
            "bound carrying a reason": {
                "status": "bound", "repository": repository, "revision": revision, "reason": "x",
            },
            "plain http": {"status": "bound", "repository": "http://example.org/r", "revision": revision},
            "scheme only": {"status": "bound", "repository": "https://", "revision": revision},
            "whitespace in URL": {"status": "bound", "repository": "https://a b", "revision": revision},
            "uppercase commit": {"status": "bound", "repository": repository, "revision": revision.upper()},
            "41 characters": {"status": "bound", "repository": repository, "revision": revision + "0"},
            "commit not a string": {"status": "bound", "repository": repository, "revision": 1},
            "unbound without reason": {"status": "unbound"},
            "empty reason": {"status": "unbound", "reason": ""},
            "blank reason": {"status": "unbound", "reason": "  "},
            "unbound carrying a repository": {
                "status": "unbound", "reason": "none", "repository": repository,
            },
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(self.janus.ManifestError) as caught:
                    self.janus.validate_manifest_obj(self._probe(source))
                self.assertEqual("J016", caught.exception.code)

    def test_the_schema_declares_the_forms_the_validator_enforces(self):
        import json

        schema = json.loads(
            (ROOT / "harness" / "schemas" / "hook-manifest.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(self.janus.REQUIRED_TOP_LEVEL, schema["required"])
        forms = {
            form["properties"]["status"]["const"]: set(form["required"])
            for form in schema["$defs"]["hostSource"]["oneOf"]
        }
        self.assertEqual(self.janus.HOST_SOURCE_KEYS, forms)
        for form in schema["$defs"]["hostSource"]["oneOf"]:
            with self.subTest(status=form["properties"]["status"]["const"]):
                self.assertFalse(form["additionalProperties"])
                self.assertEqual(set(form["required"]), set(form["properties"]))


if __name__ == "__main__":
    unittest.main()
