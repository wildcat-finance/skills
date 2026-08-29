"""Alexandria release-statement projection and hostile output-path guards."""

from copy import deepcopy
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
from unittest import mock
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"
DERIVATION_FIXTURE = FIXTURES / "credit-view-sources.json"
COMMAND = PLUGIN_ROOT / "scripts" / "alexandria.py"
ARIADNE = REPO_ROOT / "plugins" / "ariadne" / "scripts" / "ariadne.py"
ARIADNE_SAFEJSON = (
    REPO_ROOT / "plugins" / "ariadne" / "scripts" / "ariadne_lib" / "safejson.py"
)
SCHEMA = PLUGIN_ROOT / "schemas" / "release-statement-v1.schema.json"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from alexandria_lib import derive, emit_statement, ingest  # noqa: E402
from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib import statement as statement_module  # noqa: E402


def run_command(*args):
    return subprocess.run(
        [sys.executable, str(COMMAND), *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


def ariadne_input_limit():
    return runpy.run_path(str(ARIADNE_SAFEJSON))["DEFAULT_MAX_BYTES"]


class StatementTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="alexandria-statement-")
        self.root = Path(self.temporary.name).resolve()
        self.inputs = self.root / "inputs"
        shutil.copytree(FIXTURES, self.inputs)
        self.plan_path = self.inputs / "capture-plan.json"
        self.release = self.root / "release"
        self.output = self.root / "statement.json"

    def tearDown(self):
        self.temporary.cleanup()

    def build(self):
        return ingest(self.plan_path, self.release)

    def plan(self):
        return json.loads(self.plan_path.read_text(encoding="utf-8"))

    def write_plan(self, value):
        self.plan_path.write_bytes(canonical_bytes(value))

    def manifest(self, release=None):
        root = self.release if release is None else release
        return json.loads((root / "manifest.json").read_text(encoding="utf-8"))

    def build_derived(self):
        declaration = json.loads(DERIVATION_FIXTURE.read_text(encoding="utf-8"))
        inputs = self.root / "derived-inputs"
        inputs.mkdir()
        plan = {
            "format": "alexandria-capture-plan/v1",
            "release": declaration["release"],
            "components": [],
            "captures": declaration["captures"],
        }
        for component in declaration["components"]:
            component = deepcopy(component)
            source = REPO_ROOT / component.pop("repository_path")
            shutil.copy2(source, inputs / component["path"])
            plan["components"].append(component)
        plan_path = inputs / "capture-plan.json"
        plan_path.write_bytes(canonical_bytes(plan))
        raw = self.root / "mapping-raw"
        derived = self.root / "derived"
        ingest(plan_path, raw)
        derive(raw, derived)
        return derived

    def emitted(self, release=None, output=None):
        release = self.release if release is None else release
        output = self.output if output is None else output
        receipt = emit_statement(release, output)
        return receipt, json.loads(output.read_text(encoding="utf-8"))


class ProjectionTests(StatementTestCase):
    def test_raw_statement_has_exact_subjects_and_predicate_projection(self):
        release_id = self.build()
        receipt, found = self.emitted()
        manifest = self.manifest()
        release_hex = release_id.removeprefix("sha256:")

        self.assertEqual(
            receipt,
            {
                "release_id": release_id,
                "component_count": 2,
                "capture_count": 2,
                "predicate_type": statement_module.PREDICATE_TYPE,
                "output": str(self.output),
            },
        )
        self.assertEqual(
            set(found), {"_type", "subject", "predicateType", "predicate"}
        )
        self.assertEqual(found["_type"], statement_module.STATEMENT_TYPE)
        self.assertEqual(found["predicateType"], statement_module.PREDICATE_TYPE)
        self.assertEqual(
            found["subject"],
            [
                {
                    "name": "release/two-coverage-shapes",
                    "digest": {"sha256": release_hex},
                },
                *[
                    {
                        "name": f"component/{component['name']}",
                        "digest": {
                            "sha256": component["sha256"].removeprefix("sha256:")
                        },
                    }
                    for component in manifest["components"]
                ],
            ],
        )

        predicate = found["predicate"]
        self.assertEqual(set(predicate), statement_module.PREDICATE_FIELDS)
        self.assertEqual(
            predicate["release"],
            {
                "format": "alexandria-release/v1",
                "digest": {"sha256": release_hex},
            },
        )
        self.assertEqual(
            [component["name"] for component in predicate["components"]],
            [component["name"] for component in manifest["components"]],
        )
        self.assertTrue(
            all(
                set(component) == statement_module.COMPONENT_FIELDS
                for component in predicate["components"]
            )
        )
        for projected, source in zip(predicate["captures"], manifest["captures"]):
            self.assertEqual(set(projected), statement_module.CAPTURE_FIELDS)
            self.assertEqual(projected["scope"], source["scope"])
            self.assertEqual(projected["coverage"], source["coverage"])
            self.assertNotIn("source", projected)
        self.assertEqual(
            predicate["claims"],
            [
                {
                    "name": statement_module.VERIFICATION_CLAIM,
                    "subject": {"sha256": release_hex},
                    "disposition": "passed",
                }
            ],
        )
        self.assertEqual(predicate["commands"], [])
        self.assertNotIn("sha256:", self.output.read_text(encoding="utf-8"))

    def test_raw_and_derived_releases_both_emit(self):
        self.build()
        derived = self.build_derived()
        for release, name in (
            (self.release, "raw.json"),
            (derived, "derived.json"),
        ):
            with self.subTest(release=release.name):
                output = self.root / name
                receipt, found = self.emitted(release, output)
                self.assertEqual(
                    found["predicate"]["release"]["digest"]["sha256"],
                    receipt["release_id"].removeprefix("sha256:"),
                )
                self.assertEqual(
                    len(found["subject"]), receipt["component_count"] + 1
                )

    def test_heterogeneous_scopes_zero_counts_gaps_and_unsupported_are_exact(self):
        plan = self.plan()
        self.inputs.joinpath("subject-scoped.json").write_bytes(b'{"logs":[]}\n')
        coverage = plan["captures"][0]["coverage"]
        coverage["status"] = "partial"
        coverage["record_count"] = 0
        coverage["collections"][0]["record_count"] = 0
        coverage["unsupported_collections"] = ["defaults"]
        coverage["gaps"] = ["the archive omitted the requested default records"]
        self.write_plan(plan)
        self.build()
        _, found = self.emitted()

        captures = {item["id"]: item for item in found["predicate"]["captures"]}
        self.assertEqual(captures["subject-capture"]["scope"]["kind"], "subject-scoped")
        self.assertEqual(captures["full-capture"]["scope"]["interval"]["kind"], "snapshot")
        self.assertEqual(captures["subject-capture"]["coverage"]["record_count"], 0)
        self.assertEqual(
            captures["subject-capture"]["coverage"]["unsupported_collections"],
            ["defaults"],
        )
        self.assertEqual(
            captures["subject-capture"]["coverage"]["gaps"],
            ["the archive omitted the requested default records"],
        )
        self.assertEqual(captures["full-capture"]["coverage"]["gaps"], [])

    def test_repeated_emission_is_byte_identical_and_replaces_a_regular_target(self):
        self.build()
        self.output.write_bytes(b"stale\n")
        emit_statement(self.release, self.output)
        first = self.output.read_bytes()
        emit_statement(self.release, self.output)
        self.assertEqual(self.output.read_bytes(), first)
        self.assertEqual(first, canonical_bytes(json.loads(first)))

    def test_digest_conversion_refuses_prefix_length_case_and_type_faults(self):
        bad = (
            "sha512:" + "a" * 64,
            "sha256:" + "a" * 63,
            "sha256:" + "A" * 64,
            "sha256:" + "g" * 64,
            None,
        )
        for value in bad:
            with self.subTest(value=value), self.assertRaises(AlexandriaError):
                statement_module.in_toto_digest(value)

    def test_projection_validation_refuses_missing_subjects_and_changed_fields(self):
        self.build()
        manifest = self.manifest()
        complete = statement_module.statement_for(manifest)
        mutations = (
            lambda value: value["subject"].pop(),
            lambda value: value["predicate"]["components"].pop(),
            lambda value: value["predicate"]["captures"][0]["coverage"].update(
                record_count=99
            ),
        )
        for mutate in mutations:
            candidate = deepcopy(complete)
            mutate(candidate)
            with self.assertRaisesRegex(AlexandriaError, "exactly project"):
                statement_module.validate_projection(manifest, candidate)


class OutputBoundaryTests(StatementTestCase):
    def near_limit_release(self):
        data = b"{}\n"
        digest = statement_module.sha256(data)
        hexadecimal = digest.removeprefix("sha256:")
        object_path = f"objects/sha256/{hexadecimal[:2]}/{hexadecimal}"
        destination = self.release / object_path
        destination.parent.mkdir(parents=True)
        destination.write_bytes(data)
        components = [
            {
                "access": "public",
                "bytes": len(data),
                "media_type": "application/json",
                "name": f"c{index:03d}",
                "object_path": object_path,
                "redistribution": "permitted",
                "role": "raw",
                "sha256": digest,
            }
            for index in range(128)
        ]
        captures = [
            {
                "chain": "eip155:1",
                "component": "c000",
                "component_sha256": digest,
                "coverage": {
                    "collections": [],
                    "gaps": ["x" * 983] * 256,
                    "record_count": 0,
                    "status": "partial",
                    "unsupported_collections": [],
                },
                "evidence_class": "archive-log",
                "id": f"x{index:03d}",
                "scope": {
                    "deployment": "d",
                    "finality": "unknown",
                    "interval": {
                        "kind": "snapshot",
                        "observed_at": "2026-08-26T00:00:00Z",
                    },
                    "kind": "full-dataset",
                },
                "source": {
                    "kind": "local",
                    "locator_class": "local-fixture",
                    "reference": "x",
                },
                "venue": "v",
            }
            for index in range(33)
        ]
        unsigned = {
            "captures": captures,
            "components": components,
            "format": "alexandria-release/v1",
            "release": {
                "created_at": "2026-08-26T00:00:00Z",
                "name": "r",
            },
        }
        manifest = dict(unsigned)
        manifest["release_id"] = statement_module.sha256(canonical_bytes(unsigned))
        body = canonical_bytes(manifest)
        self.release.joinpath("manifest.json").write_bytes(body)
        return manifest, body

    def test_tampered_release_emits_nothing(self):
        self.build()
        manifest = self.manifest()
        component = self.release / manifest["components"][0]["object_path"]
        component.write_bytes(component.read_bytes() + b"tampered")
        with self.assertRaises(AlexandriaError):
            emit_statement(self.release, self.output)
        self.assertFalse(self.output.exists())

    def test_malformed_release_emits_nothing(self):
        self.release.mkdir()
        self.release.joinpath("manifest.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaises(AlexandriaError):
            emit_statement(self.release, self.output)
        self.assertFalse(self.output.exists())

    def test_oversized_statement_is_refused_before_replacing_output(self):
        manifest, manifest_bytes = self.near_limit_release()
        limit = ariadne_input_limit()
        self.assertLessEqual(len(manifest_bytes), limit)
        statement_bytes = canonical_bytes(statement_module.statement_for(manifest))
        self.assertGreater(len(statement_bytes), limit)
        self.output.write_bytes(b"keep\n")

        with self.assertRaisesRegex(AlexandriaError, "Ariadne's .* input limit"):
            emit_statement(self.release, self.output)

        self.assertEqual(self.output.read_bytes(), b"keep\n")

    def test_statement_limit_tracks_ariadne_bounded_reader(self):
        self.assertEqual(
            getattr(statement_module, "MAX_STATEMENT_BYTES", None),
            ariadne_input_limit(),
        )

    def test_output_inside_release_is_refused_without_mutating_the_release(self):
        self.build()
        before = {
            path.relative_to(self.release): path.read_bytes()
            for path in self.release.rglob("*")
            if path.is_file()
        }
        output = self.release / "statement.json"
        with self.assertRaisesRegex(AlexandriaError, "inside the release"):
            emit_statement(self.release, output)
        after = {
            path.relative_to(self.release): path.read_bytes()
            for path in self.release.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)
        self.assertFalse(output.exists())

    def test_symlinked_parent_into_release_is_refused(self):
        self.build()
        linked = self.root / "linked-release"
        linked.symlink_to(self.release, target_is_directory=True)
        with self.assertRaisesRegex(AlexandriaError, "inside the release"):
            emit_statement(self.release, linked / "statement.json")
        self.assertFalse((self.release / "statement.json").exists())

    def test_symlinked_missing_parent_is_refused_without_creating_outside(self):
        self.build()
        outside = self.root / "outside"
        outside.mkdir()
        linked = self.root / "link"
        linked.symlink_to(outside, target_is_directory=True)
        output = linked / "new" / "statement.json"

        result = run_command("statement", self.release, "--output", output)

        self.assertEqual(result.returncode, 1)
        self.assertIn("alexandria:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((outside / "new").exists())

    def test_parent_swap_between_inspection_and_open_is_refused(self):
        self.build()
        parent = self.root / "output-parent"
        parent.mkdir()
        held_parent = self.root / "held-output-parent"
        replacement = self.root / "replacement-parent"
        replacement.mkdir()
        output = parent / "statement.json"
        original_open = os.open
        swapped = False

        def swapping_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal swapped
            if not swapped and dir_fd is None and Path(path) == parent:
                parent.rename(held_parent)
                replacement.rename(parent)
                swapped = True
            return original_open(path, flags, mode, dir_fd=dir_fd)

        with mock.patch.object(
            statement_module.os, "open", side_effect=swapping_open
        ) as patched_open, mock.patch.object(
            statement_module.os,
            "supports_dir_fd",
            statement_module.os.supports_dir_fd | {patched_open},
        ), self.assertRaisesRegex(AlexandriaError, "parent changed"):
            emit_statement(self.release, output)
        self.assertTrue(swapped)
        self.assertFalse(output.exists())
        self.assertFalse((held_parent / "statement.json").exists())

    def test_post_open_inspection_failure_closes_parent_descriptor(self):
        self.build()
        parent = self.root / "output-parent"
        parent.mkdir()
        output = parent / "statement.json"
        original_open = os.open
        descriptors = []

        def tracking_open(path, flags, mode=0o777, *, dir_fd=None):
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
            if dir_fd is None and Path(path) == parent:
                descriptors.append(descriptor)
            return descriptor

        with mock.patch.object(
            statement_module.os, "open", side_effect=tracking_open
        ) as patched_open, mock.patch.object(
            statement_module.os,
            "supports_dir_fd",
            statement_module.os.supports_dir_fd | {patched_open},
        ), mock.patch.object(
            statement_module.os,
            "fstat",
            side_effect=OSError("inspection failed"),
        ), self.assertRaisesRegex(AlexandriaError, "cannot inspect"):
            statement_module._prepare_output(self.release, output)

        self.assertEqual(len(descriptors), 1)
        descriptor = descriptors[0]
        try:
            with self.assertRaises(OSError):
                os.fstat(descriptor)
        finally:
            try:
                os.close(descriptor)
            except OSError:
                pass

    def test_replaced_output_parent_is_refused_without_writing_through_symlink(self):
        self.build()
        parent = self.root / "output-parent"
        parent.mkdir()
        held_parent = self.root / "held-output-parent"
        outside = self.root / "outside"
        outside.mkdir()
        output = parent / "statement.json"
        original_write = statement_module._write_all

        def replace_parent(descriptor, body):
            original_write(descriptor, body)
            parent.rename(held_parent)
            parent.symlink_to(outside, target_is_directory=True)

        with mock.patch.object(
            statement_module, "_write_all", side_effect=replace_parent
        ), self.assertRaisesRegex(AlexandriaError, "parent changed"):
            emit_statement(self.release, output)
        self.assertFalse((outside / "statement.json").exists())
        self.assertFalse((held_parent / "statement.json").exists())
        self.assertEqual(list(held_parent.glob(".statement.json.tmp-*")), [])

    def test_symlinked_output_is_refused_without_touching_its_target(self):
        self.build()
        target = self.root / "target.json"
        target.write_bytes(b"keep\n")
        self.output.symlink_to(target)
        with self.assertRaisesRegex(AlexandriaError, "regular file"):
            emit_statement(self.release, self.output)
        self.assertEqual(target.read_bytes(), b"keep\n")
        self.assertTrue(self.output.is_symlink())

    def test_existing_directory_is_refused(self):
        self.build()
        self.output.mkdir()
        with self.assertRaisesRegex(AlexandriaError, "regular file"):
            emit_statement(self.release, self.output)
        self.assertTrue(self.output.is_dir())

    def test_hard_link_to_a_release_file_is_refused(self):
        self.build()
        os.link(self.release / "manifest.json", self.output)
        original = (self.release / "manifest.json").read_bytes()
        with self.assertRaisesRegex(AlexandriaError, "alias a release file"):
            emit_statement(self.release, self.output)
        self.assertEqual((self.release / "manifest.json").read_bytes(), original)
        self.assertEqual(self.output.read_bytes(), original)

    def test_interrupted_write_leaves_no_output_or_temporary_file(self):
        self.build()
        with mock.patch.object(
            statement_module, "_write_all", side_effect=OSError("interrupted")
        ), self.assertRaisesRegex(AlexandriaError, "cannot write"):
            emit_statement(self.release, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".statement.json.tmp-*")), [])

    def test_temporary_inspection_failure_closes_and_removes_created_file(self):
        parent_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        descriptors = []
        original_open = os.open

        def tracking_open(path, flags, mode=0o777, *, dir_fd=None):
            descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
            descriptors.append(descriptor)
            return descriptor

        try:
            with mock.patch.object(
                statement_module.os, "open", side_effect=tracking_open
            ), mock.patch.object(
                statement_module.os,
                "fstat",
                side_effect=OSError("inspection failed"),
            ), self.assertRaisesRegex(AlexandriaError, "cannot inspect"):
                statement_module._temporary(parent_fd, "statement.json")

            self.assertEqual(len(descriptors), 1)
            self.assertEqual(list(self.root.glob(".statement.json.tmp-*")), [])
            with self.assertRaises(OSError):
                os.fstat(descriptors[0])
        finally:
            os.close(parent_fd)

    def test_interrupted_replacement_preserves_existing_output(self):
        self.build()
        self.output.write_bytes(b"keep\n")
        with mock.patch.object(
            statement_module.os, "replace", side_effect=OSError("interrupted")
        ), self.assertRaisesRegex(AlexandriaError, "cannot write"):
            emit_statement(self.release, self.output)
        self.assertEqual(self.output.read_bytes(), b"keep\n")
        self.assertEqual(list(self.root.glob(".statement.json.tmp-*")), [])

    def test_release_change_before_install_preserves_existing_output(self):
        release_id = self.build()
        self.output.write_bytes(b"keep\n")
        with mock.patch.object(
            statement_module,
            "verify",
            side_effect=[release_id, AlexandriaError("changed")],
        ), self.assertRaisesRegex(AlexandriaError, "changed"):
            emit_statement(self.release, self.output)
        self.assertEqual(self.output.read_bytes(), b"keep\n")


class CliAndAriadneTests(StatementTestCase):
    def test_cli_emits_a_machine_readable_receipt_without_a_traceback(self):
        release_id = self.build()
        result = run_command("statement", self.release, "--output", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["release_id"], release_id)
        self.assertEqual(receipt["component_count"], 2)
        self.assertEqual(receipt["capture_count"], 2)
        self.assertEqual(receipt["predicate_type"], statement_module.PREDICATE_TYPE)

    def test_cli_reports_tampering_as_a_controlled_error(self):
        self.build()
        self.release.joinpath("manifest.json").write_text("{}\n", encoding="utf-8")
        result = run_command("statement", self.release, "--output", self.output)
        self.assertEqual(result.returncode, 1)
        self.assertIn("alexandria:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(self.output.exists())

    def test_ariadne_inspect_and_verify_keep_the_partial_boundary_visible(self):
        self.build()
        emit_statement(self.release, self.output)
        inspect = subprocess.run(
            [sys.executable, str(ARIADNE), "inspect", str(self.output)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(inspect.returncode, 0, inspect.stderr)
        self.assertIn(statement_module.PREDICATE_TYPE, inspect.stdout)
        self.assertIn("not registered here", inspect.stdout)
        self.assertIn("unsigned", inspect.stdout)

        verify = subprocess.run(
            [sys.executable, str(ARIADNE), "verify", str(self.output)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(verify.returncode, 0, verify.stderr)
        self.assertEqual(verify.stdout.count(": pass --"), 5)
        self.assertIn("gates 2 and 5", verify.stdout)
        self.assertIn("not registered here", verify.stdout)
        self.assertIn("unsigned", verify.stdout)


class SchemaDriftTests(StatementTestCase):
    def schema(self):
        return json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_schema_is_closed_and_names_the_emitter_constants(self):
        schema = self.schema()
        self.assertEqual(
            schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        self.assertEqual(
            schema["properties"]["_type"]["const"],
            statement_module.STATEMENT_TYPE,
        )
        self.assertEqual(
            schema["properties"]["predicateType"]["const"],
            statement_module.PREDICATE_TYPE,
        )
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        self.assertEqual(
            schema["properties"]["subject"]["prefixItems"],
            [{"$ref": "#/$defs/releaseSubject"}],
        )
        self.assertEqual(
            set(schema["$defs"]["predicate"]["properties"]),
            statement_module.PREDICATE_FIELDS,
        )
        self.assertEqual(
            set(schema["$defs"]["predicate"]["required"]),
            statement_module.PREDICATE_FIELDS,
        )
        self.assertEqual(
            schema["$defs"]["predicate"]["properties"]["commands"]["const"],
            [],
        )
        self.assertEqual(
            set(schema["$defs"]["component"]["properties"]),
            statement_module.COMPONENT_FIELDS,
        )
        self.assertEqual(
            set(schema["$defs"]["component"]["required"]),
            statement_module.COMPONENT_FIELDS,
        )
        self.assertEqual(
            set(schema["$defs"]["capture"]["properties"]),
            statement_module.CAPTURE_FIELDS,
        )
        self.assertEqual(
            set(schema["$defs"]["capture"]["required"]),
            statement_module.CAPTURE_FIELDS,
        )

        stack = [schema]
        objects = 0
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                if current.get("type") == "object":
                    objects += 1
                    self.assertIs(
                        current.get("additionalProperties"),
                        False,
                        current.get("title", current),
                    )
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
        self.assertGreaterEqual(objects, 10)

    def test_fixed_fixture_bytes_and_schema_field_sets_do_not_drift(self):
        self.build()
        emit_statement(self.release, self.output)
        found = json.loads(self.output.read_text(encoding="utf-8"))
        schema = self.schema()
        self.assertEqual(set(found), set(schema["properties"]))
        self.assertEqual(
            set(found["predicate"]),
            set(schema["$defs"]["predicate"]["properties"]),
        )
        self.assertEqual(
            [set(item) for item in found["predicate"]["components"]],
            [set(schema["$defs"]["component"]["properties"])] * 2,
        )
        self.assertEqual(
            [set(item) for item in found["predicate"]["captures"]],
            [set(schema["$defs"]["capture"]["properties"])] * 2,
        )
        self.assertEqual(self.output.read_bytes(), canonical_bytes(found))

    def test_every_json_file_still_parses_with_the_new_schema(self):
        for path in PLUGIN_ROOT.rglob("*.json"):
            with self.subTest(path=path):
                json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
