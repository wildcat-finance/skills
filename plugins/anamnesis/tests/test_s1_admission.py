"""Step 1: source admission refuses everything the risk register names."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"
PILOT = PLUGIN_ROOT / "specimens/pilot/policy.json"


def load():
    """Load the entrypoint by path so every test reaches the same file."""
    spec = importlib.util.spec_from_file_location("anamnesis_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anamnesis = load()


class Harness(unittest.TestCase):
    """A writable copy of the pilot whose policy each test may corrupt."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "sources").mkdir()
        self.policy = json.loads(PILOT.read_text(encoding="utf-8"))
        for source in self.policy["sources"]:
            origin = PLUGIN_ROOT / "specimens/pilot" / source["path"]
            (self.root / source["path"]).write_bytes(origin.read_bytes())

    def write(self, policy=None):
        path = self.root / "policy.json"
        path.write_text(
            json.dumps(policy if policy is not None else self.policy, indent=2),
            encoding="utf-8",
        )
        return str(path)

    def admit(self, policy=None):
        return anamnesis.admit(self.write(policy), anamnesis.Events())

    def refusal(self, policy=None):
        with self.assertRaises(anamnesis.Refusal) as caught:
            self.admit(policy)
        return caught.exception


class AdmissionSucceeds(Harness):
    def test_the_pilot_admits_every_declared_source_and_record(self):
        result = self.admit()
        self.assertEqual(len(result["sources"]), len(self.policy["sources"]))
        self.assertEqual(result["records"], len(self.policy["records"]))

    def test_the_pilot_declares_between_25_and_50_records(self):
        self.assertGreaterEqual(len(self.policy["records"]), 25)
        self.assertLessEqual(len(self.policy["records"]), 50)

    def test_every_record_names_an_admitted_source(self):
        known = {source["id"] for source in self.policy["sources"]}
        for record in self.policy["records"]:
            self.assertIn(record["source"], known)

    def test_a_zero_finding_source_is_admitted_and_contributes_no_record(self):
        named = {record["source"] for record in self.policy["records"]}
        empty = [s["id"] for s in self.policy["sources"] if s["id"] not in named]
        self.assertTrue(empty, "the pilot must carry a zero-finding round")
        self.admit()


class ClosedSchemas(Harness):
    def test_an_unknown_policy_key_is_refused(self):
        self.policy["extra"] = True
        self.assertEqual(self.refusal().code, "A011")

    def test_an_unknown_source_key_is_refused(self):
        self.policy["sources"][0]["extra"] = True
        self.assertEqual(self.refusal().code, "A011")

    def test_an_unknown_rights_key_is_refused(self):
        self.policy["sources"][0]["rights"]["extra"] = True
        self.assertEqual(self.refusal().code, "A011")

    def test_an_unknown_provenance_key_is_refused(self):
        self.policy["sources"][0]["provenance"]["extra"] = True
        self.assertEqual(self.refusal().code, "A011")

    def test_a_missing_required_key_is_refused(self):
        del self.policy["sources"][0]["producer"]
        self.assertEqual(self.refusal().code, "A012")

    def test_another_schema_identity_is_refused(self):
        self.policy["schema"] = "anamnesis-pilot-policy/v2"
        self.assertEqual(self.refusal().code, "A021")

    def test_malformed_json_is_refused(self):
        path = self.root / "policy.json"
        path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.admit(str(path), anamnesis.Events())
        self.assertEqual(caught.exception.code, "A020")


class DuplicateIdentity(Harness):
    def test_a_duplicate_source_id_is_refused(self):
        self.policy["sources"].append(copy.deepcopy(self.policy["sources"][0]))
        self.assertEqual(self.refusal().code, "A051")

    def test_a_duplicate_record_id_is_refused(self):
        self.policy["records"].append(copy.deepcopy(self.policy["records"][0]))
        self.assertEqual(self.refusal().code, "A071")

    def test_a_record_naming_an_unadmitted_source_is_refused(self):
        self.policy["records"][0]["source"] = "no-such-source"
        self.assertEqual(self.refusal().code, "A072")


class Rights(Harness):
    def test_a_missing_rights_basis_is_refused(self):
        del self.policy["sources"][0]["rights"]["basis"]
        self.assertEqual(self.refusal().code, "A012")

    def test_public_visibility_is_not_a_rights_basis(self):
        self.policy["sources"][0]["rights"]["basis"] = "public"
        refusal = self.refusal()
        self.assertEqual(refusal.code, "A030")
        self.assertIn("public visibility is not a rights basis", refusal.message)

    def test_an_unrecognised_disclosure_class_is_refused(self):
        self.policy["sources"][0]["rights"]["disclosure"] = "internal"
        self.assertEqual(self.refusal().code, "A031")

    def test_an_embargoed_source_is_refused_at_admission(self):
        self.policy["sources"][0]["rights"]["disclosure"] = "embargoed"
        self.assertEqual(self.refusal().code, "A032")

    def test_digest_only_rights_cannot_claim_public_disclosure(self):
        self.policy["sources"][0]["rights"]["basis"] = "digest-only"
        self.assertEqual(self.refusal().code, "A033")

    def test_digest_only_rights_admit_a_restricted_source(self):
        source = self.policy["sources"][0]
        source["rights"]["basis"] = "digest-only"
        source["rights"]["disclosure"] = "restricted"
        result = self.admit()
        self.assertEqual(result["sources"][0]["disclosure"], "restricted")


class Bytes(Harness):
    def test_a_digest_mismatch_is_refused(self):
        self.policy["sources"][0]["sha256"] = "0" * 64
        self.assertEqual(self.refusal().code, "A057")

    def test_a_byte_count_mismatch_is_refused(self):
        self.policy["sources"][0]["bytes"] += 1
        self.assertEqual(self.refusal().code, "A056")

    def test_a_source_above_the_declared_cap_is_refused(self):
        self.policy["max_source_bytes"] = 16
        self.assertEqual(self.refusal().code, "A054")

    def test_a_cap_above_the_absolute_ceiling_is_refused(self):
        self.policy["max_source_bytes"] = anamnesis.MAX_SOURCE_BYTES_CEILING + 1
        self.assertEqual(self.refusal().code, "A022")

    def test_bytes_on_disk_above_the_cap_are_refused_before_parsing(self):
        source = self.policy["sources"][0]
        payload = b"x" * 4096
        (self.root / source["path"]).write_bytes(payload)
        source["bytes"] = len(payload)
        source["sha256"] = hashlib.sha256(payload).hexdigest()
        self.policy["max_source_bytes"] = 2048
        self.assertEqual(self.refusal().code, "A054")


class Paths(Harness):
    def test_a_symlinked_source_is_refused(self):
        source = self.policy["sources"][0]
        target = self.root / source["path"]
        target.unlink()
        os.symlink(str(PLUGIN_ROOT / "specimens/pilot" / source["path"]), str(target))
        self.assertEqual(self.refusal().code, "A043")

    def test_a_path_escaping_the_root_is_refused(self):
        self.policy["sources"][0]["path"] = "../escape.md"
        self.assertEqual(self.refusal().code, "A041")

    def test_an_absolute_path_is_refused(self):
        self.policy["sources"][0]["path"] = "/etc/hosts"
        self.assertEqual(self.refusal().code, "A040")

    def test_a_missing_source_is_refused(self):
        self.policy["sources"][0]["path"] = "sources/absent.md"
        self.assertEqual(self.refusal().code, "A042")

    def test_a_directory_in_place_of_a_source_is_refused(self):
        source = self.policy["sources"][0]
        target = self.root / source["path"]
        target.unlink()
        target.mkdir()
        self.assertEqual(self.refusal().code, "A003")


class PilotScope(Harness):
    """The 25-to-50 range scopes the seed pilot, not admission in general."""

    def scope_refusal(self, count):
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.seed_scope(count)
        return caught.exception

    def test_fewer_than_25_records_is_outside_the_seed_scope(self):
        self.assertEqual(self.scope_refusal(10).code, "A073")

    def test_more_than_50_records_is_outside_the_seed_scope(self):
        self.assertEqual(self.scope_refusal(60).code, "A073")

    def test_the_pilot_itself_is_inside_the_seed_scope(self):
        anamnesis.seed_scope(len(self.policy["records"]))

    def test_admission_alone_does_not_enforce_the_pilot_range(self):
        """A corpus is not required to be pilot-sized to be admitted."""
        self.policy["records"] = self.policy["records"][:10]
        result = self.admit()
        self.assertEqual(result["records"], 10)


class BoundedOutput(Harness):
    def test_a_hostile_value_is_quoted_within_the_bound(self):
        self.policy["sources"][0]["media_type"] = "text/" + "A" * 5000
        refusal = self.refusal()
        self.assertEqual(refusal.code, "A052")
        self.assertLess(len(refusal.message), 400)
        self.assertIn("...", refusal.message)

    def test_the_quote_helper_bounds_any_value(self):
        self.assertLessEqual(
            len(anamnesis.quote("B" * 10_000)), anamnesis.MAX_QUOTED + 3
        )


class Events(Harness):
    def test_a_refusal_emits_its_rule_record_policy_and_correlation_id(self):
        self.policy["sources"][0]["sha256"] = "0" * 64
        events = anamnesis.Events()
        with self.assertRaises(anamnesis.Refusal):
            anamnesis.admit(self.write(), events)
        refused = [e for e in events.emitted if e["event"] == "anamnesis.source.refused"]
        self.assertEqual(len(refused), 1)
        event = refused[0]
        self.assertEqual(event["rule"], "A057")
        self.assertEqual(event["record"], self.policy["sources"][0]["id"])
        self.assertEqual(event["policy_version"], self.policy["policy_version"])
        self.assertEqual(len(event["correlation_id"]), 16)

    def test_correlation_ids_are_deterministic_across_runs(self):
        first = anamnesis.Events()
        second = anamnesis.Events()
        anamnesis.admit(self.write(), first)
        anamnesis.admit(self.write(), second)
        self.assertEqual(
            [e["correlation_id"] for e in first.emitted],
            [e["correlation_id"] for e in second.emitted],
        )

    def test_an_event_stream_is_written_as_closed_jsonl(self):
        stream = self.root / "events.jsonl"
        anamnesis.admit(self.write(), anamnesis.Events(str(stream)))
        lines = stream.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), len(self.policy["sources"]))
        for line in lines:
            event = json.loads(line)
            self.assertEqual(event["event"], "anamnesis.source.admitted")


class Report(Harness):
    def test_the_rights_report_is_the_exact_expected_object(self):
        report_path = self.root / "report.json"
        policy_path = self.write()
        command = (
            "python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py "
            f"admit-seed --policy {policy_path} --report {report_path}"
        )
        anamnesis.admit(policy_path, anamnesis.Events())
        written = anamnesis.write_report(
            str(report_path), "seed-source-rights-admitted", True, command
        )
        self.assertEqual(
            written,
            {
                "schema": "protasis-design-report/v1",
                "candidate": "anamnesis-member",
                "criterion": "seed-source-rights-admitted",
                "value": True,
                "unit": "boolean",
                "command": command,
                "exit": 0,
            },
        )
        self.assertEqual(json.loads(report_path.read_text(encoding="utf-8")), written)

    def test_no_partial_report_is_left_behind(self):
        report_path = self.root / "report.json"
        anamnesis.write_report(str(report_path), "seed-source-rights-admitted", True, "c")
        self.assertFalse((self.root / "report.json.partial").exists())


class NoNetwork(unittest.TestCase):
    def test_the_entrypoint_imports_nothing_that_reaches_a_network(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for module in ("socket", "http", "urllib", "requests", "ftplib", "smtplib"):
            self.assertNotIn(f"import {module}", source)

    def test_the_loaded_module_binds_no_network_name(self):
        for module in ("socket", "urllib", "http", "requests"):
            self.assertFalse(
                hasattr(anamnesis, module), f"{module} is reachable from the module"
            )

    def test_the_entrypoint_starts_no_subprocess(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)


class Reserved(unittest.TestCase):
    def test_curate_refuses_and_names_the_step_that_owes_it(self):
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.cmd_curate(None)
        self.assertEqual(caught.exception.code, "A090")
        self.assertIn("step 2", caught.exception.message)

    def test_release_refuses_and_names_the_step_that_owes_it(self):
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.cmd_release(None)
        self.assertEqual(caught.exception.code, "A091")
        self.assertIn("step 3", caught.exception.message)

    def test_a_refusal_exits_non_zero_without_a_traceback(self):
        self.assertEqual(anamnesis.main(["curate"]), 1)


if __name__ == "__main__":
    unittest.main()


class Recovery(Harness):
    def test_correcting_a_refused_policy_admits_on_rerun(self):
        """A refusal names its rule; repairing that rule and rerunning succeeds."""
        self.policy["sources"][0]["sha256"] = "0" * 64
        refusal = self.refusal()
        self.assertEqual(refusal.code, "A057")
        origin = PLUGIN_ROOT / "specimens/pilot/policy.json"
        self.policy["sources"][0]["sha256"] = json.loads(
            origin.read_text(encoding="utf-8")
        )["sources"][0]["sha256"]
        result = self.admit()
        self.assertEqual(len(result["sources"]), len(self.policy["sources"]))

    def test_a_refused_run_admits_nothing_at_all(self):
        """Admission is all-or-nothing: a later refusal discards earlier work."""
        self.policy["sources"][-1]["sha256"] = "0" * 64
        events = anamnesis.Events()
        with self.assertRaises(anamnesis.Refusal):
            anamnesis.admit(self.write(), events)
        self.assertEqual(
            [e["event"] for e in events.emitted][-1], "anamnesis.source.refused"
        )
