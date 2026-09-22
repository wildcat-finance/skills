"""Check the committed Wildcat metadata without accessing external releases."""

import gzip
import hashlib
import io
import json
from pathlib import Path
import unittest


EXAMPLE = Path(__file__).resolve().parents[1] / "examples/wildcat-datasets-v0"
SPEC_HASHES = {
    "study.md": "ec6813cf12117daad4e8790f786fdc6076261193b545e109cdadeb456b43fb6f",
    "runbook.md": "1b44a351f5f980b0b1787916bd84d629e90aabc14b4d35b324f96fadc7dcb2d0",
    "design-evidence.json": "4a3752781473722557fb05ab13b5f20223dbf199e2d711e0a7e790fd5287f0bb",
}
EXPECTED = {
    "v1": {
        "release_id": "sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69",
        "manifest": "a8d675d23c31e44c6c6960245a2f640b4a669e58b4cec16a350ccf859b6ee591",
        "plan": "cad23fb022e9c331793d207553de7aab6ae6e46379c757b35361932c1772dbd7",
        "registry": "4d773fde78573e1ca47ed70e3e5025d8fce3c16b55eeb362c223ea2577280bd3",
        "archive": "25322e603679a24a4d9410f24aca07696cdf83ed0349b9f86b900d246b76a687",
        "archive_bytes": 4323015,
        "subjects": 110,
        "interval": {"start": "18743513", "end": "22074622"},
    },
    "v2": {
        "release_id": "sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3",
        "manifest": "219d72f940b667c829b04f232bbebf7ee83020139faadc1ac88883c7241156f7",
        "plan": "8a70ebf145668b2fc5db99af6af2d9211d03d3f3282209ab144f9277df772482",
        "registry": "1d206f36284ce51d0d23bf843899eef27316a36e5013c3df5d81da92e72ee29f",
        "archive": "0407fecac64ff15c23d298044cd2498180ceea2900bb6807330c104b348bd90a",
        "archive_bytes": 37920375,
        "subjects": 128,
        "interval": {"start": "21866550", "end": "26022093"},
    },
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(relative):
    return json.loads((EXAMPLE / relative).read_text(encoding="utf-8"))


def read_metadata(reference):
    """Check the encoded pin before bounded decoding, then the exact source pin."""
    limit = 1048576
    size = reference["bytes"]
    encoded_size = reference["encoded_bytes"]
    if not 0 < size <= limit or not 0 < encoded_size <= limit:
        raise ValueError("metadata size exceeds limit")
    with (EXAMPLE / reference["path"]).open("rb") as stream:
        encoded = stream.read(encoded_size + 1)
    if (len(encoded) != encoded_size or
            hashlib.sha256(encoded).hexdigest() != reference["encoded_sha256"]):
        raise ValueError("encoded metadata mismatch")
    if reference["encoding"] != "gzip":
        raise ValueError("unsupported metadata encoding")
    with gzip.GzipFile(fileobj=io.BytesIO(encoded), mode="rb") as stream:
        raw = stream.read(size + 1)
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != reference["sha256"]:
        raise ValueError("decoded metadata mismatch")
    return json.loads(raw)


class WildcatMetadataTests(unittest.TestCase):
    def setUp(self):
        self.metadata = read("inputs.json")

    def test_exact_accepted_metadata_inventory(self):
        self.assertEqual(
            digest(EXAMPLE / "inputs.json"),
            "a5b56074ec07eb1114770ca4703bc53a4ef83c5e04b475d1eabacfd59bd83be8",
        )
        rows = self.metadata["files"]
        paths = [row["path"] for row in rows]
        actual = {
            path.relative_to(EXAMPLE).as_posix()
            for folder in ("inputs", "spec")
            for path in (EXAMPLE / folder).rglob("*")
            if path.is_file()
        }
        self.assertEqual(len(paths), 39)
        self.assertEqual(len(set(paths)), len(paths))
        self.assertEqual(set(paths), actual)
        for row in rows:
            with self.subTest(path=row["path"]):
                path = EXAMPLE / row["path"]
                self.assertFalse(path.is_symlink())
                self.assertEqual(path.stat().st_size, row["bytes"])
                self.assertEqual(digest(path), row["sha256"])

    def test_accepted_specification_bytes(self):
        for name, expected in SPEC_HASHES.items():
            with self.subTest(name=name):
                self.assertEqual(digest(EXAMPLE / "spec" / name), expected)

    def test_every_selection_report_is_bound(self):
        design = read("spec/design-evidence.json")
        self.assertEqual(design["selection"], {
            "candidate": "full-release", "rule": "unique-frontier", "policy_ref": None,
        })
        results = design["results"]
        pairs = {(row["candidate"], row["criterion"]) for row in results}
        criteria = {"all-files", "capture-time", "listing-bytes",
                    "existing-interface", "bad-count-refused"}
        self.assertEqual(pairs, {
            (candidate, criterion)
            for candidate in ("full-release", "manifest-only")
            for criterion in criteria
        })
        self.assertEqual(len(results), 10)
        for row in results:
            with self.subTest(candidate=row["candidate"], criterion=row["criterion"]):
                self.assertEqual(
                    digest(EXAMPLE / "spec" / row["report"]["path"]),
                    row["report"]["sha256"],
                )
                self.assertEqual(row["state"], "fail" if
                                 (row["candidate"], row["criterion"]) ==
                                 ("manifest-only", "all-files") else "pass")

    def test_estate_identities_and_archive_pins(self):
        estates = self.metadata["estates"]
        self.assertEqual([row["estate"] for row in estates], ["v1", "v2"])
        for estate in estates:
            with self.subTest(estate=estate["estate"]):
                expected = EXPECTED[estate["estate"]]
                for field in ("release_id", "subjects", "interval"):
                    self.assertEqual(estate[field], expected[field])
                for field in ("manifest", "plan", "registry"):
                    self.assertEqual(estate[field]["sha256"], expected[field])
                    read_metadata(estate[field])
                self.assertEqual(estate["archive"]["sha256"], expected["archive"])
                self.assertEqual(estate["archive"]["bytes"], expected["archive_bytes"])
                staging = read_metadata(estate["staging_manifest"])
                for field in ("sha256", "bytes", "format"):
                    self.assertEqual(staging["archive"][field], estate["archive"][field])
                self.assertEqual(len(staging["files"]), staging["staging_files_total"])
                self.assertEqual(sum(row["bytes"] for row in staging["files"]),
                                 staging["staging_bytes_total"])

    def test_manifests_preserve_inventory_and_source_coverage(self):
        for estate in self.metadata["estates"]:
            manifest = read_metadata(estate["manifest"])
            components = manifest["components"]
            self.assertEqual(manifest["release_id"], estate["release_id"])
            self.assertEqual(len(components) + 1, estate["subjects"])
            self.assertEqual(len({row["object_path"] for row in components}), len(components))
            self.assertEqual(
                sum(row["bytes"] for row in components)
                + estate["manifest"]["bytes"],
                estate["release_bytes"],
            )
            self.assertTrue(manifest["captures"])
            for capture in manifest["captures"]:
                self.assertIn("coverage", capture)
                self.assertIn("gaps", capture["coverage"])
                self.assertIn("evidence_class", capture)
            self.assertTrue(all(row["access"] == "public" for row in components))
            self.assertTrue(all(row["redistribution"] == "permitted" for row in components))

    def test_observed_rebuild_is_distinct_from_collection(self):
        revision = "104f6f82c390003fb61039d3023d07c1abe05086"
        self.assertEqual(self.metadata["source_revision"], revision)
        self.assertEqual(self.metadata["signature_status"], "unsigned")
        self.assertIn("no new rebuild", self.metadata["verification_boundary"])
        for estate in self.metadata["estates"]:
            observed = estate["observed_rebuild"]
            self.assertEqual(observed["runtime_commit"], revision)
            self.assertEqual(observed["python"], "3.14.6")
            self.assertEqual(observed["exit"], 0)
            self.assertEqual(observed["argv"][:4], [
                "python3",
                "plugins/alexandria/examples/wildcat-"
                + estate["estate"] + "-interval-v0/demo.py",
                "build", "--output",
            ])
            self.assertTrue((EXAMPLE / observed["report"]).is_file())
            historical = read_metadata(estate["original_collection"]["evidence"])
            if estate["estate"] == "v1":
                self.assertNotEqual(historical["runtime"]["source_commit"], revision)
            else:
                self.assertNotIn("commands", historical)
                self.assertIn("not established", estate["original_collection"]["argv_status"])
        recovery = read("inputs/observations/rebuild-recovery.json")
        self.assertEqual(recovery["reproduced"]["exit"], 1)
        self.assertEqual(recovery["recovery"]["build_exit"], 0)
        self.assertNotEqual(recovery["reproduced"]["old_staging"],
                            recovery["recovery"]["staging"])

    def test_saved_verification_reports_keep_their_original_digests(self):
        observations = read("inputs/observations/inputs.json")
        self.assertEqual(len(observations), 2)
        for estate in observations:
            self.assertEqual(len(estate["commands"]), 2)
            for command in estate["commands"]:
                name = Path(command["report"]).name
                self.assertEqual(command["exit"], 0)
                self.assertEqual(digest(EXAMPLE / "inputs/observations" / name),
                                 command["sha256"])

    def test_compressed_metadata_checks_encoded_and_decoded_pins(self):
        reference = self.metadata["estates"][0]["manifest"]
        for change, message in [
            ({"encoded_sha256": "0" * 64}, "encoded metadata mismatch"),
            ({"encoded_bytes": reference["encoded_bytes"] - 1}, "encoded metadata mismatch"),
            ({"sha256": "0" * 64}, "decoded metadata mismatch"),
            ({"bytes": reference["bytes"] - 1}, "decoded metadata mismatch"),
            ({"bytes": 1048577}, "metadata size exceeds limit"),
            ({"encoding": "unknown"}, "unsupported metadata encoding"),
        ]:
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, message):
                    read_metadata(dict(reference, **change))

    def test_every_compressed_source_has_a_decoded_pin(self):
        references = {}
        for estate in self.metadata["estates"]:
            for value in estate.values():
                if isinstance(value, dict) and value.get("encoding") == "gzip":
                    references[value["path"]] = value
        compressed = {row["path"]: row for row in self.metadata["files"]
                      if row["path"].endswith(".gz")}
        self.assertEqual(set(references), set(compressed))
        self.assertEqual(len(references), 14)
        for name, reference in references.items():
            with self.subTest(path=name):
                self.assertEqual(reference["encoded_sha256"], compressed[name]["sha256"])
                self.assertEqual(reference["encoded_bytes"], compressed[name]["bytes"])
                read_metadata(reference)


if __name__ == "__main__":
    unittest.main()
