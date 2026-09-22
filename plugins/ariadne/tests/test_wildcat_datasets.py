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
    "runbook.md": "551c4004901f54ab120ae5a740a50fc183b08861516b337a32f9201e27159ec5",
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
            "95fe70b1ffc78e55fb4f2e7c92915d47504e8e2d05350819fbc54c4df24e314a",
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


# The real demonstrations are required delivery evidence; these small specimens
# exercise hostile inputs independently of the external archives.
import copy
import importlib.util
import os
import shutil
import socket
import tempfile
from unittest.mock import patch

DEMO_SPEC = importlib.util.spec_from_file_location('wildcat_dataset_demo', EXAMPLE / 'demo.py')
DEMO = importlib.util.module_from_spec(DEMO_SPEC)
DEMO_SPEC.loader.exec_module(DEMO)


class WildcatAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.metadata = DEMO.load_inputs()

    def specimen(self):
        release = self.root / 'release'
        release.mkdir()
        data = b'{"records":[{"number":1},{"number":2}]}\n'
        (release / 'data.json').write_bytes(data)
        return release, [{'path': 'data.json', 'sha256': DEMO.sha(data), 'bytes': len(data),
                          'record_count': 2, 'selector': '/records'}]

    def test_selector_count_is_derived_from_array(self):
        root, rows = self.specimen()
        self.assertEqual(DEMO.check_release(root, rows), root)
        rows[0]['record_count'] = 3
        with self.assertRaisesRegex(DEMO.DemoError, 'selector record count mismatch'):
            DEMO.check_release(root, rows)

    def test_non_array_selector_cannot_count_as_record(self):
        root, rows = self.specimen()
        data = b'{"records":{"number":1}}'
        (root / 'data.json').write_bytes(data)
        rows[0].update(bytes=len(data), sha256=DEMO.sha(data), record_count=1)
        with self.assertRaisesRegex(DEMO.DemoError, 'selector record count mismatch'):
            DEMO.check_release(root, rows)

    def test_missing_extra_and_changed_file_refuse(self):
        root, rows = self.specimen()
        source = (root / 'data.json').read_bytes()
        (root / 'extra').write_bytes(b'')
        with self.assertRaisesRegex(DEMO.DemoError, 'file inventory mismatch'):
            DEMO.check_release(root, rows)
        (root / 'extra').unlink()
        (root / 'data.json').unlink()
        (root / 'different').write_bytes(source)
        with self.assertRaisesRegex(DEMO.DemoError, 'file inventory mismatch'):
            DEMO.check_release(root, rows)
        (root / 'different').rename(root / 'data.json')
        (root / 'data.json').write_bytes(source.replace(b'1', b'9'))
        with self.assertRaisesRegex(DEMO.DemoError, 'file digest mismatch'):
            DEMO.check_release(root, rows)

    def test_wrong_manifest_bytes_refuse(self):
        root, rows = self.specimen()
        (root / 'data.json').write_bytes(b'{}')
        with self.assertRaisesRegex(DEMO.DemoError, 'size mismatch'):
            DEMO.check_release(root, rows)

    def test_manifest_identity_count_and_selector_refuse(self):
        estate = self.metadata['estates'][0]
        original = DEMO.metadata_document(estate['manifest'])
        mutations = [
            (lambda m: m.update(release_id='sha256:' + '0' * 64), 'release identity'),
            (lambda m: m['components'].pop(), 'subject inventory'),
            (lambda m: m['captures'][0]['coverage']['collections'][0].update(selector='/made-up'), 'unsupported count'),
            (lambda m: m['captures'][0]['coverage'].update(record_count=True), 'conflicting record counts'),
            (lambda m: m['components'][0].update(object_path='../escape'), 'unsafe relative path'),
            (lambda m: m['components'][0].update(sha256='sha256:' + '0' * 64), 'path and digest'),
        ]
        for mutate, message in mutations:
            with self.subTest(message=message):
                manifest = copy.deepcopy(original)
                mutate(manifest)
                with self.assertRaisesRegex(DEMO.DemoError, message):
                    DEMO.release_rows(estate, manifest)

    def test_unsafe_relative_paths_refuse(self):
        for value in ('../file', '/file', 'a//b', 'a/./b', 'a\\b', ''):
            with self.subTest(value=value), self.assertRaises(DEMO.DemoError):
                DEMO.relative(value)

    def test_symlink_root_parent_and_file_refuse(self):
        root, rows = self.specimen()
        link = self.root / 'link'
        link.symlink_to(root, target_is_directory=True)
        with self.assertRaisesRegex(DEMO.DemoError, 'symlink'):
            DEMO.check_release(link, rows)
        with self.assertRaisesRegex(DEMO.DemoError, 'symlink'):
            DEMO.safe_path(link / 'data.json')
        (root / 'data.json').unlink()
        (root / 'data.json').symlink_to(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            DEMO.check_release(root, rows)

    def test_fifo_refuses_before_open(self):
        path = self.root / 'fifo'
        os.mkfifo(path)
        with self.assertRaisesRegex(DEMO.DemoError, 'regular file'):
            DEMO.read_bytes(path, 10)

    def test_metadata_size_and_encoding_refuse(self):
        ref = self.metadata['estates'][0]['manifest']
        for field, value in [('bytes', True), ('bytes', 1048577), ('encoded_bytes', 0),
                             ('encoded_sha256', '0' * 64), ('sha256', '0' * 64),
                             ('encoding', 'unknown'), ('path', '../escape')]:
            with self.subTest(field=field), self.assertRaises(DEMO.DemoError):
                DEMO.metadata_document(dict(ref, **{field: value}))

    def test_existing_destination_is_unchanged(self):
        root, _ = self.specimen()
        before = (root / 'data.json').read_bytes()
        with self.assertRaisesRegex(DEMO.DemoError, 'already exists'):
            DEMO.write_outputs(root, {'data.json': b'wrong'})
        self.assertEqual((root / 'data.json').read_bytes(), before)

    def test_output_alias_refuses_before_capture(self):
        v1 = self.root / 'v1'
        v2 = self.root / 'v2'
        v1.mkdir()
        v2.mkdir()
        env = {'ARIADNE_WILDCAT_V1_RELEASE': str(v1), 'ARIADNE_WILDCAT_V2_RELEASE': str(v2)}
        with patch.dict(os.environ, env), patch.object(DEMO, 'observed_outputs', side_effect=AssertionError('capture ran')):
            with self.assertRaisesRegex(DEMO.DemoError, 'alias or containment'):
                DEMO.main(['build', '--output', str(v1 / 'output')])
            with self.assertRaisesRegex(DEMO.DemoError, 'alias or containment'):
                DEMO.main(['verify', '--output', str(self.root)])

    def test_complete_reports_and_real_coverage_mutations(self):
        for estate in ('v1', 'v2'):
            statement = DEMO.read_json((EXAMPLE / 'preserved' / estate / 'statement.json').read_bytes())
            report = DEMO.report_for(statement)
            self.assertTrue(report.ok)
            self.assertEqual(len(report.gates), 10)
            self.assertFalse(report.document.signed)
            self.assertEqual(report.unchecked, [])
            for mutation in ('missing-gap', 'missing-reason', 'outside-bound'):
                result = DEMO.report_for(DEMO.coverage_mutation(statement, mutation))
                self.assertEqual([g.name for g in result.gates if not g.passed], ['coverage'])

    def test_incomplete_output_and_forged_gate_report_refuse(self):
        root = self.root / 'output'
        expected = {'verify.json': b'{"ok":false}\n', 'statement.json': b'{}\n'}
        DEMO.write_outputs(root, expected)
        DEMO.compare_outputs(root, expected)
        (root / 'verify.json').write_bytes(b'{"ok":true}\n')
        with self.assertRaisesRegex(DEMO.DemoError, 'output content mismatch'):
            DEMO.compare_outputs(root, expected)
        (root / 'verify.json').unlink()
        with self.assertRaisesRegex(DEMO.DemoError, 'output inventory mismatch'):
            DEMO.compare_outputs(root, expected)

    def test_preserved_verification_does_not_read_external_releases(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(DEMO, 'check_release', side_effect=AssertionError('external read')):
            outputs = DEMO.preserved_outputs(self.metadata)
            DEMO.compare_outputs(EXAMPLE / 'preserved', outputs)
            self.assertEqual(DEMO.main(['verify-preserved']), 0)

    def test_modified_preserved_statement_and_report_refuse(self):
        replica = self.root / 'example'
        shutil.copytree(EXAMPLE, replica, ignore=shutil.ignore_patterns('__pycache__'))
        statement_path = replica / 'preserved/v1/statement.json'
        original = DEMO.read_json(statement_path.read_bytes())
        for mutate, message in [
            (lambda s: s['predicate']['dataset_subjects'][0].update(record_count=999), 'subject or input'),
            (lambda s: s['predicate']['producer'].update(tool='invented'), 'producer'),
            (lambda s: s['predicate']['claims'][0].update(detail='invented'), 'claims'),
            (lambda s: s['predicate']['coverage']['gaps'].clear(), 'coverage'),
            (lambda s: s['predicate']['deltas'].update(reason='invented'), 'first-release'),
        ]:
            with self.subTest(message=message):
                candidate = copy.deepcopy(original)
                mutate(candidate)
                statement_path.write_bytes(DEMO.encoded(candidate))
                with patch.object(DEMO, 'EXAMPLE', replica), self.assertRaisesRegex(DEMO.DemoError, message):
                    DEMO.preserved_outputs(self.metadata)
        statement_path.write_bytes(DEMO.encoded(original))
        report = replica / 'preserved/v2/verify.json'
        report.write_text('{"ok":true}')
        with patch.object(DEMO, 'EXAMPLE', replica):
            with self.assertRaisesRegex(DEMO.DemoError, 'content mismatch: v2/verify.json'):
                DEMO.compare_outputs(replica / 'preserved', DEMO.preserved_outputs(self.metadata))

    def test_socket_guard_observes_and_refuses_attempt(self):
        def attempts_socket(*args):
            socket.socket()
        with patch.object(DEMO, 'build_estate', attempts_socket):
            with self.assertRaisesRegex(DEMO.DemoError, 'socket use refused'):
                DEMO.observed_outputs(self.metadata, {'v1': self.root, 'v2': self.root})

    def test_unsigned_null_baselines_and_full_inventories(self):
        for estate in self.metadata['estates']:
            name = estate['estate']
            statement = DEMO.read_json((EXAMPLE / 'preserved' / name / 'statement.json').read_bytes())
            body = statement['predicate']
            self.assertEqual(len(body['dataset_subjects']), estate['subjects'])
            self.assertEqual(len(statement['subject']), estate['subjects'] + 1)
            self.assertIsNone(body['deltas']['baseline'])
            self.assertIn('separate estates', body['deltas']['reason'])
            coverage = DEMO.read_json((EXAMPLE / 'preserved' / name / 'coverage.json').read_bytes())
            manifest = DEMO.metadata_document(estate['manifest'])
            self.assertEqual(coverage['captures'], manifest['captures'])
            self.assertEqual(coverage['components'], manifest['components'])
