"""Schema 2 and schema 3 releases, and every named row refusal."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from . import support
from tabularium_lib import CURRENT_EVENT_SCHEMA, SUPPORTED_EVENT_SCHEMAS
from tabularium_lib.builder import build
from tabularium_lib.core import TabulariumError, canonical_json, jsonl_bytes, sha256_bytes
from tabularium_lib.verifier import verify


COMMAND = support.PLUGIN_ROOT / "scripts" / "tabularium.py"
EXAMPLES = support.PLUGIN_ROOT / "examples"
SOURCE_FIXTURE = support.FIXTURES / "minimal-snapshot.json"
CAPTURE_FIXTURE = support.FIXTURES / "minimal-capture-manifest.json"
PUBLISHED_V0 = (
    ("aave-v4-v0", "aave-v4", "aave-v4-mainnet-credit-window-v0"),
    ("euler-v1-v0", "euler-v1", "euler-v1-borrow-block-14531589-v0"),
    ("euler-v2-v0", "euler-v2", "euler-v2-owner-activity-1786933919-v0"),
)


def run(*args):
    return subprocess.run(
        [sys.executable, str(COMMAND), *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


class SupportedSchemaSetTests(unittest.TestCase):
    def test_the_library_names_the_versions_it_reads_and_the_one_it_writes(self):
        self.assertEqual(SUPPORTED_EVENT_SCHEMAS, frozenset({2, 3}))
        self.assertEqual(CURRENT_EVENT_SCHEMA, 3)
        self.assertIn(CURRENT_EVENT_SCHEMA, SUPPORTED_EVENT_SCHEMAS)


class SchemaVersionReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.json"
        self.capture = self.root / "capture.json"
        self.canonical = self.root / "events.jsonl"
        self.manifest_path = self.root / "coverage.json"
        self.source.write_bytes(SOURCE_FIXTURE.read_bytes())
        self.capture.write_bytes(CAPTURE_FIXTURE.read_bytes())

    def make(self, event_schema=CURRENT_EVENT_SCHEMA):
        return build(
            self.source,
            self.capture,
            self.canonical,
            self.manifest_path,
            "fixture-v1",
            event_schema=event_schema,
        )

    def manifest(self):
        return json.loads(self.manifest_path.read_text())

    def rows(self):
        return [json.loads(line) for line in self.canonical.read_text().splitlines()]

    def rewrite(self, rows, manifest=None):
        data = jsonl_bytes(rows)
        self.canonical.write_bytes(data)
        manifest = self.manifest() if manifest is None else manifest
        manifest["canonical"]["sha256"] = sha256_bytes(data)
        manifest["canonical"]["bytes"] = len(data)
        self.manifest_path.write_bytes(canonical_json(manifest) + b"\n")

    def refuse_row(self, change, expected):
        self.make()
        rows = self.rows()
        change(rows[0])
        self.rewrite(rows)
        with self.assertRaisesRegex(TabulariumError, expected):
            verify(self.manifest_path)

    def test_build_writes_the_current_schema_by_default(self):
        self.make()
        self.assertEqual(self.manifest()["schema_version"], 3)
        self.assertEqual(self.manifest()["versions"]["event_schema"], 3)
        self.assertEqual({row["schema_version"] for row in self.rows()}, {3})

    def test_build_refuses_an_event_schema_outside_the_supported_set(self):
        with self.assertRaisesRegex(TabulariumError, "requested event schema version 4"):
            self.make(event_schema=4)
        self.assertFalse(self.canonical.exists())
        self.assertFalse(self.manifest_path.exists())

    def test_verify_accepts_both_supported_schema_versions(self):
        for version in sorted(SUPPORTED_EVENT_SCHEMAS):
            with self.subTest(version=version):
                self.make(event_schema=version)
                report = verify(self.manifest_path)
                self.assertEqual(report.schema_version, version)
                self.assertEqual(report.rows, 2)

    def test_a_row_below_the_manifest_version_is_refused(self):
        self.make(event_schema=3)
        rows = self.rows()
        rows[0]["schema_version"] = 2
        self.rewrite(rows)
        with self.assertRaisesRegex(
            TabulariumError,
            "canonical row 1 field schema_version is 2, not the release schema version 3",
        ):
            verify(self.manifest_path)

    def test_a_row_above_the_manifest_version_is_refused(self):
        self.make(event_schema=2)
        rows = self.rows()
        rows[0]["schema_version"] = 3
        self.rewrite(rows)
        with self.assertRaisesRegex(
            TabulariumError,
            "canonical row 1 field schema_version is 3, not the release schema version 2",
        ):
            verify(self.manifest_path)

    def test_a_manifest_event_schema_unlike_its_own_version_is_refused(self):
        self.make(event_schema=3)
        manifest = self.manifest()
        manifest["versions"]["event_schema"] = 2
        self.manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(
            TabulariumError,
            "versions.event_schema 2 is not coverage manifest.schema_version 3",
        ):
            verify(self.manifest_path)

    def test_an_unknown_venue_is_refused_by_name(self):
        self.refuse_row(
            lambda row: row.__setitem__("venue", "compound-v3"),
            "canonical row 1 field venue is 'compound-v3'",
        )

    def test_an_unknown_adapter_is_refused_by_name(self):
        self.refuse_row(
            lambda row: row["provenance"].__setitem__("adapter", "euler-v1"),
            "canonical row 1 field provenance.adapter is 'euler-v1'",
        )

    def test_an_unknown_adapter_version_is_refused_by_name(self):
        self.refuse_row(
            lambda row: row["provenance"].__setitem__("adapter_version", "1.0.0"),
            "canonical row 1 field provenance.adapter_version is '1.0.0'",
        )

    def test_an_unknown_protocol_generation_is_refused_by_name(self):
        self.refuse_row(
            lambda row: row["provenance"].__setitem__("protocol_generation", "euler-v2"),
            "canonical row 1 field provenance.protocol_generation is 'euler-v2'",
        )

    def test_an_unknown_source_api_is_refused_by_name(self):
        self.refuse_row(
            lambda row: row["provenance"].__setitem__("source_api", "euler-v3"),
            "canonical row 1 field provenance.source_api is 'euler-v3'",
        )

    def test_an_unknown_mapping_rule_is_refused_by_name(self):
        self.refuse_row(
            lambda row: row["provenance"].__setitem__("mapping_rule", "euler-v1.borrow.v1"),
            "canonical row 1 field provenance.mapping_rule is 'euler-v1.borrow.v1'",
        )

    def test_a_missing_provenance_field_is_refused_by_name(self):
        self.refuse_row(
            lambda row: row["provenance"].pop("source_api"),
            "canonical row 1 has no field provenance.source_api",
        )

    def test_an_unknown_evidence_class_is_refused_by_name(self):
        self.make()
        manifest = self.manifest()
        manifest["source"]["evidence_class"] = "hosted-rpc-reported-log-scope"
        self.manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(
            TabulariumError,
            "source.evidence_class 'hosted-rpc-reported-log-scope'",
        ):
            verify(self.manifest_path)

    def test_the_success_line_carries_the_schema_version(self):
        self.make()
        result = run("verify", self.manifest_path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("schema 3, sha256", result.stdout)

    def test_a_refused_row_reaches_stderr_at_exit_one(self):
        self.make()
        rows = self.rows()
        rows[0]["provenance"]["source_api"] = "euler-v3"
        self.rewrite(rows)
        result = run("verify", self.manifest_path)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "canonical row 1 field provenance.source_api is 'euler-v3'", result.stderr
        )
        self.assertEqual(result.stdout, "")

    def test_the_cli_refuses_an_event_schema_outside_the_supported_set(self):
        result = run(
            "build",
            "--source", self.source,
            "--capture-manifest", self.capture,
            "--out", self.canonical,
            "--manifest", self.manifest_path,
            "--release", "fixture-v1",
            "--event-schema", "4",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--event-schema", result.stderr)
        self.assertFalse(self.canonical.exists())
        self.assertFalse(self.manifest_path.exists())


class PublishedScheme2ReleaseTests(unittest.TestCase):
    def test_event_schema_two_reproduces_every_published_release_byte_for_byte(self):
        for directory, adapter, release_id in PUBLISHED_V0:
            with self.subTest(release=release_id):
                published = EXAMPLES / directory
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    source = root / "source.json"
                    capture = root / "capture.json"
                    canonical = root / "events.jsonl"
                    manifest = root / "coverage.json"
                    source.write_bytes((published / "source.json").read_bytes())
                    capture.write_bytes((published / "capture.json").read_bytes())
                    build(
                        source,
                        capture,
                        canonical,
                        manifest,
                        release_id,
                        adapter,
                        event_schema=2,
                    )
                    for name, rebuilt in (
                        ("events.jsonl", canonical),
                        ("coverage.json", manifest),
                    ):
                        self.assertEqual(
                            rebuilt.read_bytes(), (published / name).read_bytes()
                        )
                    self.assertEqual(verify(manifest).schema_version, 2)


if __name__ == "__main__":
    unittest.main()
