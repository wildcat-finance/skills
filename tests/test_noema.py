"""Scaffold and hostile-boundary tests for the Noema shadow prototype."""

from __future__ import annotations

import contextlib
from hashlib import sha256
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "noema.py"
SCHEMA = ROOT / "schemas" / "noema-v1.schema.json"
INVENTORY = ROOT / "tests" / "fixtures" / "noema-v1" / "seed-inventory.json"
STUDY = ROOT / "docs" / "noema" / "study.md"
RUNBOOK = ROOT / "docs" / "noema" / "runbook.md"
NOEMA_FIXTURES = ROOT / "tests" / "fixtures" / "noema-v1"
CODEC_FIXTURE = NOEMA_FIXTURES / "codec" / "complete.noe"
MODULES_FIXTURE = NOEMA_FIXTURES / "modules"
PROFILE_FIXTURE = NOEMA_FIXTURES / "profiles" / "ascii-baseline.json"
KERNEL_FIXTURE = NOEMA_FIXTURES / "profiles" / "kernel.noe"
CORE_DIGEST = "df97b7f39b31fcad8d75fe6d7079b12ee7c8326bd4ec1758a6577764ad1b6b76"
BOUND_SOURCE = NOEMA_FIXTURES / "codec" / "bound-source.txt"
SOURCE_DIGEST = "34a6411e347aa461190a71ceaa666418923ac947101c4d6db2f5e62f2b386dac"
RUNTIME_FIXTURE = NOEMA_FIXTURES / "runtime"


def load_noema():
    """Load the repository entrypoint without relying on import-path state."""
    spec = importlib.util.spec_from_file_location("noema_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


noema = load_noema()


def scratch_directory(prefix="noema-"):
    """Return transient in-repository space below the ignored scratch root."""
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def source_binding(start: int = 0, end: int = 1):
    return [
        "src",
        "tests/fixtures/noema-v1/codec/bound-source.txt",
        SOURCE_DIGEST,
        str(start),
        str(end),
    ]


def base_records(directive=None, *, literals=None, definitions=None):
    records = [["import", "core", CORE_DIGEST]]
    records.extend(literals or [])
    records.extend(definitions or [])
    records.append(
        [
            "rule",
            "rule.test",
            directive or ["+", ["core.ready", [":", "state", "ready"]]],
            source_binding(),
        ]
    )
    return records


def compile_records(records):
    raw = noema._canonical_source(records)
    return noema.compile_source(raw, MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)


def checked_fact(proposition, value="true", label="fact"):
    return {
        "id": noema.fact_id(proposition),
        "value": value,
        "evidence_sha256": sha256(label.encode()).hexdigest(),
    }


def runtime_selection(
    operation,
    *,
    state="blocked",
    target="repository",
    tools=(),
    authority=(),
    facts=(),
):
    return {
        "operation": operation,
        "state": state,
        "target": target,
        "tools": sorted(tools),
        "authority": sorted(authority),
        "facts": sorted(facts, key=lambda item: item["id"]),
    }


def select_records(records, selection):
    build, artifacts = compile_records(records)
    profile = noema._decode_json(artifacts["profile"], "profile", canonical=True)
    manifest, projection = noema.select_runtime(
        build,
        profile,
        sha256(artifacts["profile"]).hexdigest(),
        selection,
    )
    return build, manifest, projection


def runtime_fixture(selection_name="selection.json"):
    build, _raw, artifacts = noema.load_build(
        RUNTIME_FIXTURE / "build.json",
        RUNTIME_FIXTURE / "modules",
        RUNTIME_FIXTURE / "profile.json",
        RUNTIME_FIXTURE / "kernel.noe",
    )
    selection, _raw = noema._read_canonical_json(
        RUNTIME_FIXTURE / selection_name,
        "selection",
    )
    profile = noema._decode_json(artifacts["profile"], "profile", canonical=True)
    manifest, projection = noema.select_runtime(
        build,
        profile,
        sha256(artifacts["profile"]).hexdigest(),
        selection,
    )
    return build, selection, manifest, projection


def write_bytes(path: Path, payload: bytes) -> None:
    """Write one test-owned file below its disposable directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def nested_proposition(wrappers):
    proposition = [
        "=",
        [":", "state", "ready"],
        [":", "state", "ready"],
    ]
    for _index in range(wrappers):
        proposition = ["~", proposition]
    return proposition


def assert_build_and_projection_round_trip(test, build, artifacts, modules):
    profile = noema._decode_json(
        artifacts["profile"],
        "profile",
        canonical=True,
    )
    with tempfile.TemporaryDirectory() as temporary:
        build_path = Path(temporary) / "build.json"
        write_bytes(build_path, artifacts["build"])
        actions = (
            (
                "build",
                lambda: noema.load_build(
                    build_path,
                    modules,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )[0],
                build,
            ),
            (
                "projection",
                lambda: noema.recover_projection(
                    noema.project_build(
                        build,
                        profile,
                        build["lock"]["profile_sha256"],
                    ),
                    profile,
                ),
                build["graph"],
            ),
        )
        for name, action, expected in actions:
            with test.subTest(name=name):
                try:
                    recovered = action()
                except noema.Refusal as raised:
                    test.fail(
                        f"maximum-depth {name} round trip refused: {raised.code}"
                    )
                test.assertEqual(recovered, expected)


def zip_info(name: str, kind: int = stat.S_IFREG, compression: int = zipfile.ZIP_DEFLATED):
    """Return one Unix-attributed ZipInfo for a hostile fixture."""
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    info.compress_type = compression
    permissions = 0o755 if kind == stat.S_IFDIR else 0o644
    info.external_attr = (kind | permissions) << 16
    if kind == stat.S_IFDIR:
        info.external_attr |= 0x10
    return info


def archive_bytes(
    files: list[tuple[str, bytes]],
    *,
    root: str = "seed/",
    include_root: bool = True,
    special: tuple[str, int, bytes] | None = None,
    compression: int = zipfile.ZIP_DEFLATED,
) -> bytes:
    """Build one bounded archive entirely in memory."""
    import io

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        if include_root:
            archive.writestr(zip_info(root, stat.S_IFDIR, compression), b"")
        for name, payload in files:
            archive.writestr(zip_info(root + name, stat.S_IFREG, compression), payload)
        if special is not None:
            name, kind, payload = special
            archive.writestr(zip_info(root + name, kind, compression), payload)
    return output.getvalue()


def inventory_for(payload: bytes, files: list[tuple[str, bytes]], *, root: str = "seed/"):
    """Return the exact closed inventory for one synthetic archive."""
    return {
        "schema": noema.INVENTORY_SCHEMA,
        "archive": {
            "name": "noema-v0-evidence.zip",
            "url": "https://example.invalid/noema-v0-evidence.zip",
            "bytes": len(payload),
            "sha256": sha256(payload).hexdigest(),
            "root": root,
        },
        "files": [
            {
                "path": name,
                "bytes": len(content),
                "sha256": sha256(content).hexdigest(),
            }
            for name, content in sorted(files)
        ],
    }


def write_case(
    directory: Path,
    files: list[tuple[str, bytes]],
    *,
    payload: bytes | None = None,
    inventory: dict[str, object] | None = None,
    **archive_options,
) -> tuple[Path, Path]:
    """Write one archive/inventory pair and return both paths."""
    encoded = payload if payload is not None else archive_bytes(files, **archive_options)
    record = inventory if inventory is not None else inventory_for(
        encoded, files, root=archive_options.get("root", "seed/")
    )
    archive_path = directory / "seed.zip"
    inventory_path = directory / "inventory.json"
    write_bytes(archive_path, encoded)
    write_bytes(
        inventory_path,
        (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode(),
    )
    return archive_path, inventory_path


def refusal(archive_path: Path, inventory_path: Path) -> noema.Refusal:
    """Return the stable refusal for one invalid pair."""
    with unittest.TestCase().assertRaises(noema.Refusal) as raised:
        noema.verify_seed(archive_path, inventory_path)
    return raised.exception


class NoemaScaffoldTests(unittest.TestCase):
    def test_receipted_study_copy_is_exact(self):
        self.assertEqual(
            sha256(STUDY.read_bytes()).hexdigest(),
            "4a7c0e7bdfc3d44535d36d3666b3272436d1662463aabc6c82380bd554e5ffec",
        )

    def test_receipted_runbook_copy_is_exact(self):
        self.assertEqual(
            sha256(RUNBOOK.read_bytes()).hexdigest(),
            "3984d411c2ad227764e5807fa711bbc6ae2cec46043333c8c4fb4958853408e2",
        )

    def test_repository_python_pin_is_exact(self):
        self.assertEqual((ROOT / ".python-version").read_text().strip(), "3.14.6")

    def test_schema_is_closed_and_names_all_record_families(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            set(schema), {"$schema", "$id", "title", "oneOf", "$defs"}
        )
        public_records = {
            "seedInventory", "module", "profile", "build", "projection",
            "semanticDiff", "lock", "manifest", "sliceProjection", "result",
            "evidence",
        }
        self.assertEqual(
            public_records,
            {reference["$ref"].rsplit("/", 1)[-1] for reference in schema["oneOf"]},
        )
        for name in public_records:
            self.assertFalse(schema["$defs"][name]["additionalProperties"])

    def test_schema_rejects_noncanonical_archive_member_paths(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        pattern = schema["$defs"]["relativePath"]["pattern"]
        for path in ("a/./b", "a//b", "a/"):
            with self.subTest(path=path):
                self.assertIsNone(re.fullmatch(pattern, path))

    def test_runtime_path_alphabets_match_the_published_schema(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            noema.SEED_RELATIVE_PATH_RE.pattern,
            schema["$defs"]["relativePath"]["pattern"],
        )
        self.assertEqual(
            noema.SEED_ROOT_PATH_RE.pattern,
            schema["$defs"]["seedInventory"]["properties"]["archive"]
            ["properties"]["root"]["pattern"],
        )

    def test_schema_closes_graph_tuple_shapes(self):
        definitions = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]
        self.assertEqual(set(definitions["term"]), {"oneOf"})
        term_tags = set()
        call_branches = 0
        for branch in definitions["term"]["oneOf"]:
            head = branch["prefixItems"][0]
            if "const" in head:
                term_tags.add(head["const"])
            elif "enum" in head:
                term_tags.update(head["enum"])
            else:
                self.assertEqual(head, {"$ref": "#/$defs/qualifiedIdentifier"})
                call_branches += 1
        self.assertEqual(term_tags, set(noema.TERM_TAGS | noema.OPERATORS))
        self.assertEqual(call_branches, 1)
        source_records = {
            branch["prefixItems"][0]["const"]: branch
            for branch in definitions["sourceRecord"]["oneOf"]
        }
        expected_arities = {
            "import": 3,
            "literal": 5,
            "definition": 4,
            "rule": 4,
            "precedence": 6,
            "override": 7,
            "transition": 8,
            "promise": 11,
            "handoff": 11,
            "exception": 9,
        }
        for form, arity in expected_arities.items():
            with self.subTest(form=form):
                self.assertEqual(len(source_records[form]["prefixItems"]), arity)
                self.assertEqual(source_records[form]["minItems"], arity)
                self.assertEqual(source_records[form]["maxItems"], arity)
        for collection, item_ref in {
            "types": "#/$defs/typeDeclaration",
            "signatures": "#/$defs/signature",
            "definitions": "#/$defs/moduleDefinition",
        }.items():
            self.assertEqual(
                definitions["module"]["properties"][collection]["items"]["$ref"],
                item_ref,
            )
        self.assertEqual(
            definitions["profile"]["properties"]["reserved"],
            {"const": sorted(noema.RESERVED_SYMBOLS)},
        )
        self.assertEqual(
            definitions["identifier"]["not"], {"pattern": r"\.\."}
        )

    def test_schema_covers_every_emitted_result_dimension(self):
        definitions = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]
        digest_dimensions = set(definitions["digestSet"]["properties"])
        count_dimensions = set(definitions["countSet"]["properties"])
        self.assertTrue(
            {"archive", "inventory", "source", "graph", "build", "profile",
             "projection", "before", "after", "diff"} <= digest_dimensions
        )
        self.assertTrue(
            {"bytes", "members", "records", "modules", "aliases", "entries"}
            <= count_dimensions
        )

    def test_maximum_definition_refusal_field_fits_the_result_schema(self):
        name = "local." + "x" * 122
        records = base_records(
            definitions=[
                [
                    "definition",
                    name,
                    [],
                    ["=", [":", "actor", "x"], [":", "scope", "x"]],
                ]
            ]
        )
        try:
            compile_records(records)
        except noema.Refusal as raised:
            result = noema._result(
                "parse",
                "refuse",
                raised.code,
                field=raised.field,
                message=raised.message,
            )
        else:
            self.fail("unlike definition operands compiled")
        maximum = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"][
            "result"
        ]["properties"]["field"]["maxLength"]
        self.assertEqual(len(result["field"]), 144)
        self.assertLessEqual(len(result["field"]), maximum)

    def test_contract_magic_and_about_result_are_fixed(self):
        self.assertEqual((noema.CONTRACT, noema.SOURCE_MAGIC, noema.PROJECTION_MAGIC),
                         ("noema/v1", "NOE1", "NT1"))
        result = noema.about()
        self.assertEqual(result["schema"], "noema-result/v1")
        self.assertEqual(result["code"], "NOE-I-ABOUT")
        self.assertEqual(result["verdict"], "ok")
        self.assertRegex(result["correlation_id"], r"^[0-9a-f]{64}$")

    def test_cli_help_names_only_scaffold_and_reserved_operations(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("verify-seed", completed.stdout)
        for command in noema.UNIMPLEMENTED:
            self.assertIn(command, completed.stdout)

    def test_every_reserved_operation_refuses_with_one_json_line(self):
        for command in noema.UNIMPLEMENTED:
            with self.subTest(command=command):
                completed = subprocess.run(
                    [sys.executable, str(SCRIPT), command],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stderr, "")
                self.assertEqual(len(completed.stdout.splitlines()), 1)
                result = json.loads(completed.stdout)
                self.assertEqual(result["code"], "NOE-E-UNIMPLEMENTED")
                self.assertEqual(result["command"], command)
                self.assertEqual(result["verdict"], "refuse")

    def test_malformed_cli_is_bounded_json_without_argument_echo(self):
        hostile = "x" * 200_000
        for arguments, expected_command in (
            (["about", hostile], "about"),
            ([hostile], "invalid"),
        ):
            with self.subTest(expected_command=expected_command):
                stdout = io.StringIO()
                stderr = io.StringIO()
                try:
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        status = noema.main(arguments)
                except SystemExit as error:
                    status = error.code
                self.assertEqual(status, 2)
                self.assertEqual(stderr.getvalue(), "")
                self.assertNotIn(hostile, stdout.getvalue())
                self.assertLess(len(stdout.getvalue().encode("utf-8")), 1_024)
                lines = stdout.getvalue().splitlines()
                self.assertEqual(len(lines), 1)
                result = json.loads(lines[0])
                self.assertEqual(result["command"], expected_command)
                self.assertEqual(result["code"], "NOE-E-TYPE.ARGUMENTS")
                self.assertEqual(result["verdict"], "refuse")

        commands = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]["result"]["properties"]["command"]["enum"]
        self.assertIn("invalid", commands)

    def test_committed_seed_inventory_has_exact_public_shape(self):
        inventory, raw = noema.load_inventory(INVENTORY)
        self.assertEqual(len(inventory["files"]), 17)
        self.assertEqual(inventory["archive"]["bytes"], 24_907)
        self.assertEqual(
            inventory["archive"]["sha256"],
            "1e1eb5e9908551f1337b7ec58a37ae7f37fd97e41d5ac424bc4992eb1d11b540",
        )
        self.assertEqual(sha256(raw).hexdigest(), sha256(INVENTORY.read_bytes()).hexdigest())

    def test_valid_synthetic_archive_verifies_without_extraction(self):
        files = [("a.txt", b"alpha\n"), ("nested.json", b"{}\n")]
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(Path(temporary), files)
            before = set(Path(temporary).iterdir())
            result = noema.verify_seed(archive_path, inventory_path)
            self.assertEqual(result["code"], "NOE-OK")
            self.assertEqual(result["counts"]["members"], 2)
            self.assertEqual(set(Path(temporary).iterdir()), before)

    def test_archive_byte_cap_refuses_before_zip_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            archive_path = directory / "oversized.zip"
            write_bytes(archive_path, b"z" * (noema.MAX_ARCHIVE_BYTES + 1))
            _, inventory_path = write_case(directory / "record", [("a", b"a")])
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-BOUNDS.FILE")

    def test_member_count_cap_includes_the_root_directory(self):
        files = [(f"f{index:02}.txt", b"x") for index in range(noema.MAX_MEMBERS)]
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(Path(temporary), files)
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-BOUNDS.MEMBERS")

    def test_inventory_rejects_one_member_above_its_byte_cap(self):
        files = [("a.txt", b"a")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["files"][0]["bytes"] = noema.MAX_MEMBER_BYTES + 1
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-BOUNDS.INTEGER")

    def test_inventory_rejects_aggregate_member_bytes_above_cap(self):
        files = [("a", b"a"), ("b", b"b")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["files"][0]["bytes"] = 600_000
        record["files"][1]["bytes"] = 600_000
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-BOUNDS.TOTAL")

    def test_duplicate_archive_member_refuses(self):
        files = [("a.txt", b"alpha")]
        import io

        output = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(output, "w") as archive:
                archive.writestr(zip_info("seed/", stat.S_IFDIR), b"")
                archive.writestr(zip_info("seed/a.txt"), b"alpha")
                archive.writestr(zip_info("seed/a.txt"), b"alpha")
        payload = output.getvalue()
        record = inventory_for(payload, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-REFERENCE.DUPLICATE_MEMBER")

    def test_extra_archive_member_refuses(self):
        expected = [("a.txt", b"alpha")]
        payload = archive_bytes(expected + [("extra.txt", b"extra")])
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-REFERENCE.EXTRA_MEMBER")

    def test_traversal_archive_member_refuses(self):
        expected = [("a.txt", b"alpha")]
        payload = archive_bytes([("../escape", b"alpha")])
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.TRAVERSAL")

    def test_absolute_archive_member_refuses(self):
        expected = [("a.txt", b"alpha")]
        payload = archive_bytes([], include_root=True)
        import io

        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr(zip_info("seed/", stat.S_IFDIR), b"")
            archive.writestr(zip_info("/absolute.txt"), b"alpha")
        payload = output.getvalue()
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.ROOT")

    def test_backslash_archive_member_refuses(self):
        expected = [("a.txt", b"alpha")]
        payload = archive_bytes([("bad\\name", b"alpha")])
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.RELATIVE")

    def test_noncanonical_archive_member_path_refuses(self):
        for name in ("a/./b", "a//b"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                files = [(name, b"alpha")]
                archive_path, inventory_path = write_case(Path(temporary), files)
                error = refusal(archive_path, inventory_path)
                self.assertEqual(error.code, "NOE-E-PATH.RELATIVE")

    def test_noncanonical_archive_root_refuses(self):
        files = [("a.txt", b"alpha")]
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, root="seed//"
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.ROOT")

    def test_schema_invalid_archive_member_path_refuses(self):
        for name in ("a b", "C:policy"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                files = [(name, b"alpha")]
                archive_path, inventory_path = write_case(Path(temporary), files)
                error = refusal(archive_path, inventory_path)
                self.assertEqual(error.code, "NOE-E-PATH.RELATIVE")

    def test_schema_invalid_archive_root_refuses(self):
        files = [("a.txt", b"alpha")]
        for root in ("seed space/", "C:seed/"):
            with self.subTest(root=root), tempfile.TemporaryDirectory() as temporary:
                archive_path, inventory_path = write_case(
                    Path(temporary), files, root=root
                )
                error = refusal(archive_path, inventory_path)
                self.assertEqual(error.code, "NOE-E-PATH.ROOT")

    def test_descriptor_read_failure_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input"
            write_bytes(path, b"alpha")
            with mock.patch.object(
                noema.os, "read", side_effect=OSError("injected read fault")
            ), self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(path, "archive", 16)
            self.assertEqual(raised.exception.code, "NOE-E-IO.READ")

    def test_descriptor_inspection_failure_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input"
            write_bytes(path, b"alpha")
            with mock.patch.object(
                noema.os, "fstat", side_effect=OSError("injected fstat fault")
            ), self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(path, "archive", 16)
            self.assertEqual(raised.exception.code, "NOE-E-IO.READ")

    def test_descriptor_close_failure_refuses(self):
        real_close = os.close

        def close_then_fail(descriptor):
            real_close(descriptor)
            raise OSError("injected close fault")

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input"
            write_bytes(path, b"alpha")
            with mock.patch.object(
                noema.os, "close", side_effect=close_then_fail
            ), self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(path, "archive", 16)
            self.assertEqual(raised.exception.code, "NOE-E-IO.READ")

    def test_symbolic_link_archive_member_refuses(self):
        expected = [("link", b"target")]
        payload = archive_bytes([], special=("link", stat.S_IFLNK, b"target"))
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.SPECIAL")

    def test_fifo_archive_member_refuses(self):
        expected = [("pipe", b"")]
        payload = archive_bytes([], special=("pipe", stat.S_IFIFO, b""))
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.SPECIAL")

    def test_unsupported_archive_compression_refuses(self):
        if not hasattr(zipfile, "ZIP_BZIP2"):
            self.skipTest("BZIP2 Zip support is unavailable")
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files, compression=zipfile.ZIP_BZIP2)
        record = inventory_for(payload, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-SYNTAX.COMPRESSION")

    def test_corrupt_deflate_member_refuses(self):
        import io

        files = [("a.txt", b"alpha" * 8)]
        payload = bytearray(archive_bytes(files))
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            info = archive.getinfo("seed/a.txt")
            compressed_start = (
                info.header_offset
                + 30
                + len(info.filename.encode("utf-8"))
                + len(info.extra)
            )
        payload[compressed_start] ^= 0x55
        corrupted = bytes(payload)
        record = inventory_for(corrupted, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=corrupted, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-SYNTAX.ZIP")

    def test_archive_digest_mismatch_refuses_before_member_read(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["archive"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-DIGEST.ARCHIVE")

    def test_member_size_mismatch_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["files"][0]["bytes"] = 4
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-DIGEST.MEMBER_SIZE")

    def test_member_digest_mismatch_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["files"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-DIGEST.MEMBER")

    def test_missing_root_directory_entry_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files, include_root=False)
        record = inventory_for(payload, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-REFERENCE.ROOT")

    def test_duplicate_inventory_key_refuses(self):
        text = (
            '{"schema":"noema-seed-inventory/v1",'
            '"schema":"noema-seed-inventory/v1","archive":{},"files":[]}'
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "inventory.json"
            write_bytes(path, text.encode())
            with self.assertRaises(noema.Refusal) as raised:
                noema.load_inventory(path)
            self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.DUPLICATE_KEY")

    def test_inventory_extra_key_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["extra"] = True
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-TYPE.KEYS")

    def test_lone_surrogate_inventory_string_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["archive"]["url"] = "https://example.invalid/\ud800"
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-SYNTAX.UNICODE")

    def test_invalid_utf8_archive_name_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = bytearray(archive_bytes(files))
        local = payload.index(b"PK\x03\x04")
        central = payload.index(b"PK\x01\x02")
        for header, flag_offset, name_offset in (
            (local, 6, 30),
            (central, 8, 46),
        ):
            flags = int.from_bytes(payload[header + flag_offset:header + flag_offset + 2], "little")
            payload[header + flag_offset:header + flag_offset + 2] = (flags | 0x800).to_bytes(2, "little")
            payload[header + name_offset] = 0xFF
        malformed = bytes(payload)
        record = inventory_for(malformed, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=malformed, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-SYNTAX.ZIP")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_symbolic_link_archive_path_refuses(self):
        files = [("a.txt", b"alpha")]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            archive_path, inventory_path = write_case(directory, files)
            linked = directory / "linked.zip"
            linked.symlink_to(archive_path)
            error = refusal(linked, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.REGULAR")


class CanonicalSourceTests(unittest.TestCase):
    def test_checked_in_source_is_byte_identical_after_format(self):
        raw = CODEC_FIXTURE.read_bytes()
        build, artifacts = noema.compile_source(raw, MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        self.assertEqual(artifacts["source"], raw)
        self.assertEqual(noema._canonical_source(build["graph"]["records"]), raw)

    def test_noncanonical_json_spacing_refuses(self):
        raw = b'NOE1\n["import", "core","' + CORE_DIGEST.encode() + b'"]\n'
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(raw)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.CANONICAL")

    def test_missing_final_lf_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE1")
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.FINAL_LF")

    def test_extra_final_lf_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE1\n\n")
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.LINES")

    def test_cr_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE1\r\n")
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.LINES")

    def test_wrong_magic_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE0\n")
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.MAGIC")

    def test_record_order_refuses(self):
        records = base_records()
        records.reverse()
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_duplicate_record_key_refuses(self):
        records = base_records()
        records.append(records[-1])
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_unknown_record_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            compile_records([["wat", "x"]])
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.RECORD")

    def test_duplicate_json_key_refuses(self):
        raw = b'NOE1\n{"x":1,"x":2}\n'
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(raw)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.DUPLICATE_KEY")

    def test_line_cap_accepts_exact_and_refuses_plus_one(self):
        exact_line = b'"' + b"a" * (noema.MAX_LINE_BYTES - 3) + b'"\n'
        self.assertEqual(len(exact_line), noema.MAX_LINE_BYTES)
        self.assertEqual(len(noema._parse_source_lines(b"NOE1\n" + exact_line)), 1)
        too_long = b'"' + b"a" * (noema.MAX_LINE_BYTES - 2) + b'"\n'
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE1\n" + too_long)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.LINE")

    def test_input_cap_accepts_exact_and_refuses_plus_one(self):
        remaining = noema.MAX_INPUT_BYTES - len(b"NOE1\n")
        lines = []
        while remaining:
            size = min(noema.MAX_LINE_BYTES, remaining)
            if size < 3:
                take = 3 - size
                lines[-1] = lines[-1][:-take]
                remaining += take
                continue
            lines.append(b'"' + b"a" * (size - 3) + b'"\n')
            remaining -= size
        exact = b"NOE1\n" + b"".join(lines)
        self.assertEqual(len(exact), noema.MAX_INPUT_BYTES)
        noema._parse_source_lines(exact)
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(exact + b"0\n")
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.FILE")

    def test_record_cap_accepts_exact_and_refuses_plus_one(self):
        exact = b"NOE1\n" + b"[]\n" * noema.MAX_RECORDS
        self.assertEqual(len(noema._parse_source_lines(exact)), noema.MAX_RECORDS)
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(exact + b"[]\n")
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.RECORDS")

    def test_literal_cap_accepts_exact_and_refuses_plus_one(self):
        value = "x" * noema.MAX_LITERAL_BYTES
        literal = ["literal", "lit.big", "text", str(noema.MAX_LITERAL_BYTES), value]
        compile_records(base_records(literals=[literal]))
        literal[4] += "x"
        literal[3] = str(noema.MAX_LITERAL_BYTES + 1)
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(literals=[literal]))
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.STRING")

    def test_literal_aggregate_cap_accepts_exact_and_refuses_plus_one(self):
        sizes = [65_000] * 12 + [6_432]
        literals = [
            ["literal", f"lit.{index:02d}", "text", str(size), "x" * size]
            for index, size in enumerate(sizes)
        ]
        compile_records(base_records(literals=literals))
        literals[-1][3] = "6433"
        literals[-1][4] += "x"
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(literals=literals))
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.LITERAL_TOTAL")

    def test_import_cap_accepts_exact_and_refuses_plus_one(self):
        exact = [["import", f"m{index:02d}", "0" * 64] for index in range(noema.MAX_IMPORTS)]
        imports, _definitions = noema._preflight_records(exact)
        self.assertEqual(len(imports), noema.MAX_IMPORTS)
        extra = exact + [["import", "mz", "0" * 64]]
        with self.assertRaises(noema.Refusal) as raised:
            noema._preflight_records(extra)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.IMPORTS")

    def test_finite_set_cap_accepts_exact_and_refuses_plus_one(self):
        literals = [
            ["literal", f"n{index:04d}", "number", "1", "1"]
            for index in range(noema.MAX_SET_MEMBERS + 1)
        ]
        members = [["$", f"n{index:04d}"] for index in range(noema.MAX_SET_MEMBERS)]
        quantified = ["all", ["x", "value"], ["{}", "value", *members], ["=", ["%", "x"], ["$", "n0000"]]]
        compile_records(base_records(["+", quantified], literals=literals[:-1]))
        quantified[2].append(["$", f"n{noema.MAX_SET_MEMBERS:04d}"])
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(["+", quantified], literals=literals))
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.SET")

    def test_very_long_decimal_never_enters_integer_conversion(self):
        literal = ["literal", "n", "number", "65000", "9" * 65_000]
        compile_records(base_records(literals=[literal]))


class GraphValidationTests(unittest.TestCase):
    def test_macro_expansion_counts_repeated_parameter_substitution(self):
        self.assertEqual(4 * (2**14), noema.MAX_EXPANDED_NODES)
        definitions = [
            [
                "definition",
                "local.dup",
                [["x", "proposition"]],
                ["&", ["%", "x"], ["%", "x"]],
            ]
        ]

        def expanded(levels):
            proposition = [
                "=",
                [":", "state", "ready"],
                [":", "state", "ready"],
            ]
            for _index in range(levels):
                proposition = ["local.dup", proposition]
            return proposition

        compile_records(
            base_records(["+", expanded(14)], definitions=definitions)
        )
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(
                base_records(
                    ["+", ["~", expanded(14)]],
                    definitions=definitions,
                )
            )
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.EXPANSION")

    def test_maximum_depth_source_build_and_projection_round_trip(self):
        records = base_records(
            ["+", nested_proposition(noema.MAX_DEPTH - 5)]
        )
        build, artifacts = compile_records(records)
        assert_build_and_projection_round_trip(
            self,
            build,
            artifacts,
            MODULES_FIXTURE,
        )

        with self.assertRaises(noema.Refusal) as raised:
            compile_records(
                base_records(
                    ["+", nested_proposition(noema.MAX_DEPTH - 4)]
                )
            )
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.DEPTH")

    def test_container_record_and_term_tags_refuse_without_raw_type_errors(self):
        cases = (
            ([[[]]], "NOE-E-TYPE.RECORD"),
            (
                base_records(
                    definitions=[["definition", "local.bad", [], [[]]]]
                ),
                "NOE-E-TYPE.TERM",
            ),
        )
        for records, code in cases:
            with self.subTest(code=code):
                try:
                    compile_records(records)
                except noema.Refusal as raised:
                    self.assertEqual(raised.code, code)
                except TypeError:
                    self.fail("container tag escaped the refusal channel")
                else:
                    self.fail("container tag compiled")

    def test_structural_results_cannot_be_minted_by_typed_atoms(self):
        for directive in (
            [":", "directive", "anything"],
            ["+", [":", "proposition", "anything"]],
            ["+", ["=", [":", "relation", "anything"], [":", "relation", "anything"]]],
        ):
            with self.subTest(directive=directive):
                try:
                    compile_records(base_records(directive))
                except noema.Refusal as raised:
                    self.assertEqual(raised.code, "NOE-E-TYPE.STRUCTURAL_ATOM")
                else:
                    self.fail("typed atom minted a structural result")

    def test_source_bindings_require_utf8_and_scalar_boundaries(self):
        modules = noema._load_modules(MODULES_FIXTURE, [("core", CORE_DIGEST)])
        for payload, end, code in (
            (b"\xff", 1, "NOE-E-SYNTAX.SOURCE_UTF8"),
            ("é".encode("utf-8"), 1, "NOE-E-REFERENCE.SPAN_UTF8"),
        ):
            records = base_records()
            records[-1][3][2] = sha256(payload).hexdigest()
            records[-1][3][4] = str(end)
            source = noema._canonical_source(records)
            with self.subTest(payload=payload):
                with mock.patch.object(
                    noema, "_read_regular", return_value=payload
                ), mock.patch.object(
                    noema,
                    "_read_repository_regular",
                    return_value=(payload, (1, 1)),
                    create=True,
                ), self.assertRaises(noema.Refusal) as raised:
                    noema._compile_records(records, modules, source)
                self.assertEqual(raised.exception.code, code)

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_source_binding_refuses_a_linked_ancestor(self):
        with scratch_directory(
            prefix="noema-source-"
        ) as inside, tempfile.TemporaryDirectory(prefix="noema-outside-") as outside:
            inside_path = Path(inside)
            payload = b"x"
            (Path(outside) / "payload.txt").write_bytes(payload)
            (inside_path / "escape").symlink_to(outside, target_is_directory=True)
            relative = (
                inside_path.relative_to(ROOT) / "escape" / "payload.txt"
            ).as_posix()
            records = base_records()
            records[-1][3] = [
                "src",
                relative,
                sha256(payload).hexdigest(),
                "0",
                "1",
            ]
            modules = noema._load_modules(MODULES_FIXTURE, [("core", CORE_DIGEST)])
            with self.assertRaises(noema.Refusal) as raised:
                noema._compile_records(
                    records,
                    modules,
                    noema._canonical_source(records),
                )
            self.assertEqual(raised.exception.code, "NOE-E-PATH.CONFINEMENT")

    def test_finite_set_members_are_unique_and_canonically_ordered(self):
        duplicate = ["+", ["in", [":", "actor", "a"], ["{}", "actor", [":", "actor", "a"], [":", "actor", "a"]]]]
        reversed_members = ["+", ["in", [":", "actor", "a"], ["{}", "actor", [":", "actor", "b"], [":", "actor", "a"]]]]
        for directive in (duplicate, reversed_members):
            with self.subTest(directive=directive):
                with self.assertRaises(noema.Refusal) as raised:
                    compile_records(base_records(directive))
                self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.SET_ORDER")

    def test_unknown_operator_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(["wat", [":", "state", "ready"]]))
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.OPERATOR")

    def test_wrong_arity_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(["+", [":", "effect", "x"], [":", "effect", "y"]]))
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.ARITY")

    def test_type_mismatch_refuses(self):
        directive = ["@", [":", "actor", "alice"], ["+", [":", "effect", "x"]]]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(directive))
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.MISMATCH")

    def test_unresolved_literal_refuses(self):
        directive = ["+", ["core.invokes", [":", "effect", "x"], ["$", "absent"]]]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(directive))
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.LITERAL")

    def test_unresolved_predicate_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(["+", ["core.absent"]]))
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.PREDICATE")

    def test_definition_cycle_refuses(self):
        definitions = [
            ["definition", "local.a", [], ["local.b"]],
            ["definition", "local.b", [], ["local.a"]],
        ]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(definitions=definitions))
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.DEFINITION_CYCLE")

    def test_precedence_cycle_refuses(self):
        records = [["import", "core", CORE_DIGEST]]
        records.extend(
            [
                ["rule", "a", ["+", [":", "effect", "x"]], source_binding(0, 1)],
                ["rule", "b", ["+", [":", "effect", "y"]], source_binding(1, 2)],
                ["precedence", "a", "b", [":", "actor", "x"], [":", "scope", "x"], [":", "evidence", "x"]],
                ["precedence", "b", "a", [":", "actor", "x"], [":", "scope", "x"], [":", "evidence", "x"]],
            ]
        )
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.RELATION_CYCLE")

    def test_override_and_mixed_relation_cycles_refuse(self):
        actor = [":", "actor", "x"]
        scope = [":", "scope", "x"]
        evidence = [":", "evidence", "x"]
        prefix = [
            ["import", "core", CORE_DIGEST],
            ["rule", "a", ["+", [":", "effect", "x"]], source_binding(0, 1)],
            ["rule", "b", ["+", [":", "effect", "y"]], source_binding(1, 2)],
        ]
        for relations in (
            [
                ["override", "o1", actor, "a", "b", scope, evidence],
                ["override", "o2", actor, "b", "a", scope, evidence],
            ],
            [
                ["precedence", "a", "b", actor, scope, evidence],
                ["override", "o1", actor, "b", "a", scope, evidence],
            ],
        ):
            with self.subTest(relations=relations):
                try:
                    compile_records(prefix + relations)
                except noema.Refusal as raised:
                    self.assertEqual(
                        raised.code,
                        "NOE-E-REFERENCE.RELATION_CYCLE",
                    )
                else:
                    self.fail("cyclic governing relation compiled")

    def test_long_acyclic_definition_chain_does_not_recurse(self):
        count = 1_200
        definitions = [
            ["definition", f"local.d{index:04d}", [], [f"local.d{index + 1:04d}"]]
            for index in range(count - 1)
        ]
        definitions.append(
            ["definition", f"local.d{count - 1:04d}", [], [":", "effect", "x"]]
        )
        try:
            compile_records(
                base_records(["+", ["local.d0000"]], definitions=definitions)
            )
        except RecursionError:
            self.fail("acyclic definition chain reached the interpreter recursion limit")

    def test_long_acyclic_precedence_chain_does_not_recurse(self):
        count = 1_500
        source_digest = sha256(SCRIPT.read_bytes()).hexdigest()
        records = [["import", "core", CORE_DIGEST]]
        records.extend(
            [
                [
                    "rule",
                    f"r{index:04d}",
                    ["+", [":", "effect", "x"]],
                    ["src", "scripts/noema.py", source_digest, str(index), str(index + 1)],
                ]
                for index in range(count)
            ]
        )
        records.extend(
            [
                [
                    "precedence",
                    f"r{index:04d}",
                    f"r{index + 1:04d}",
                    [":", "actor", "x"],
                    [":", "scope", "x"],
                    [":", "evidence", "x"],
                ]
                for index in range(count - 1)
            ]
        )
        try:
            compile_records(records)
        except RecursionError:
            self.fail("acyclic precedence chain reached the interpreter recursion limit")

    def test_overlapping_source_spans_refuse(self):
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "a", ["+", [":", "effect", "x"]], source_binding(0, 2)],
            ["rule", "b", ["+", [":", "effect", "y"]], source_binding(1, 3)],
        ]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.SPAN")

    def test_graph_node_budget_refuses_limit_plus_one(self):
        budget = noema._Budget()
        for _index in range(noema.MAX_GRAPH_NODES):
            budget.node("test")
        with self.assertRaises(noema.Refusal) as raised:
            budget.node("test")
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.NODES")


class ModuleLockTests(unittest.TestCase):
    @staticmethod
    def module_bytes(
        module_id,
        *,
        imports=None,
        types=None,
        signatures=None,
        definitions=None,
    ):
        return noema._canonical_json(
            {
                "schema": "noema-module/v1",
                "id": module_id,
                "imports": imports or [],
                "types": types or [],
                "signatures": signatures or [],
                "definitions": definitions or [],
            }
        )

    def _module_chain(self, directory, count):
        child = None
        child_digest = None
        root_digest = None
        for index in reversed(range(count)):
            module_id = f"m{index:02d}"
            value = {
                "schema": noema.MODULE_SCHEMA,
                "id": module_id,
                "imports": [] if child is None else [[child, child_digest]],
                "types": [],
                "signatures": [],
                "definitions": [],
            }
            raw = noema._canonical_json(value)
            (directory / f"{module_id}.json").write_bytes(raw)
            child = module_id
            child_digest = sha256(raw).hexdigest()
            root_digest = child_digest
        return root_digest

    def _signature_module(self, directory, count):
        value = {
            "schema": noema.MODULE_SCHEMA,
            "id": "m",
            "imports": [],
            "types": [],
            "signatures": [
                [f"m.p{index:05d}", [], "value"] for index in range(count)
            ],
            "definitions": [],
        }
        raw = noema._canonical_json(value)
        (directory / "m.json").write_bytes(raw)
        return sha256(raw).hexdigest()

    def test_maximum_depth_module_build_and_projection_round_trip(self):
        def module_at(wrappers):
            return self.module_bytes(
                "m",
                definitions=[["m.deep", [], nested_proposition(wrappers)]],
            )

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            module = module_at(noema.MAX_DEPTH - 6)
            write_bytes(directory / "m.json", module)
            records = [
                ["import", "m", sha256(module).hexdigest()],
                ["rule", "rule.test", ["+", ["m.deep"]], source_binding()],
            ]
            build, artifacts = noema.compile_source(
                noema._canonical_source(records),
                directory,
                PROFILE_FIXTURE,
                KERNEL_FIXTURE,
            )
            assert_build_and_projection_round_trip(
                self,
                build,
                artifacts,
                directory,
            )

            too_deep = module_at(noema.MAX_DEPTH - 5)
            write_bytes(directory / "m.json", too_deep)
            too_deep_records = [
                ["import", "m", sha256(too_deep).hexdigest()],
                ["rule", "rule.test", ["+", ["m.deep"]], source_binding()],
            ]
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(
                    noema._canonical_source(too_deep_records),
                    directory,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )
            self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.DEPTH")

    def test_lock_binds_every_dependency_byte_string(self):
        build, artifacts = noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        lock = build["lock"]
        self.assertEqual(lock["source_sha256"], sha256(artifacts["source"]).hexdigest())
        self.assertEqual(lock["graph_sha256"], sha256(artifacts["graph"]).hexdigest())
        self.assertEqual(lock["kernel_sha256"], sha256(KERNEL_FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(lock["profile_sha256"], sha256(PROFILE_FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(lock["modules"], [{"id": "core", "sha256": CORE_DIGEST}])

    def test_stale_module_digest_refuses(self):
        records = base_records()
        records[0][2] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MODULE")

    def test_absent_module_refuses(self):
        records = [["import", "absent", "0" * 64]]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-IO.READ")

    def test_ambient_module_file_is_not_loaded(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "core.json").write_bytes((MODULES_FIXTURE / "core.json").read_bytes())
            (directory / "ambient.json").write_text("not json\n")
            raw = noema._canonical_source(base_records())
            build, _artifacts = noema.compile_source(raw, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual([item["id"] for item in build["graph"]["modules"]], ["core"])

    def test_module_symbol_requires_its_declared_import_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            child = self.module_bytes(
                "b",
                signatures=[["b.pred", [], "proposition"]],
            )
            child_digest = sha256(child).hexdigest()
            parent = self.module_bytes(
                "a",
                definitions=[["a.ready", [], ["b.pred"]]],
            )
            write_bytes(directory / "a.json", parent)
            write_bytes(directory / "b.json", child)
            records = [
                ["import", "a", sha256(parent).hexdigest()],
                ["import", "b", child_digest],
                ["rule", "rule.test", ["+", ["a.ready"]], source_binding()],
            ]
            try:
                noema.compile_source(
                    noema._canonical_source(records),
                    directory,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )
            except noema.Refusal as raised:
                self.assertEqual(
                    raised.code,
                    "NOE-E-REFERENCE.MODULE_AMBIENT",
                )
            else:
                self.fail("module used a source co-import as an ambient dependency")

            parent = self.module_bytes(
                "a",
                imports=[["b", child_digest]],
                definitions=[["a.ready", [], ["b.pred"]]],
            )
            write_bytes(directory / "a.json", parent)
            records[0][2] = sha256(parent).hexdigest()
            build, _artifacts = noema.compile_source(
                noema._canonical_source(records),
                directory,
                PROFILE_FIXTURE,
                KERNEL_FIXTURE,
            )
            self.assertEqual(
                [item["id"] for item in build["graph"]["modules"]],
                ["a", "b"],
            )

    def test_module_definition_cannot_bind_a_source_local_definition(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            module = self.module_bytes(
                "a",
                definitions=[["a.ready", [], ["local.helper"]]],
            )
            write_bytes(directory / "a.json", module)
            records = [
                ["import", "a", sha256(module).hexdigest()],
                [
                    "definition",
                    "local.helper",
                    [],
                    ["=", [":", "state", "ready"], [":", "state", "ready"]],
                ],
                ["rule", "rule.test", ["+", ["a.ready"]], source_binding()],
            ]
            try:
                noema.compile_source(
                    noema._canonical_source(records),
                    directory,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )
            except noema.Refusal as raised:
                self.assertEqual(
                    raised.code,
                    "NOE-E-REFERENCE.MODULE_AMBIENT",
                )
            else:
                self.fail("module bound a source-local definition")

    def test_module_cannot_capture_the_source_local_namespace(self):
        for module_id in ("local", "local.vendor"):
            with self.subTest(module_id=module_id), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                module = self.module_bytes(
                    module_id,
                    definitions=[
                        [
                            f"{module_id}.ready",
                            [],
                            ["=", [":", "state", "ready"], [":", "state", "ready"]],
                        ]
                    ],
                )
                write_bytes(directory / f"{module_id}.json", module)
                records = [
                    ["import", module_id, sha256(module).hexdigest()],
                    [
                        "rule",
                        "rule.test",
                        ["+", [f"{module_id}.ready"]],
                        source_binding(),
                    ],
                ]
                try:
                    noema.compile_source(
                        noema._canonical_source(records),
                        directory,
                        PROFILE_FIXTURE,
                        KERNEL_FIXTURE,
                    )
                except noema.Refusal as raised:
                    self.assertEqual(
                        raised.code,
                        "NOE-E-REFERENCE.MODULE_NAMESPACE",
                    )
                else:
                    self.fail("module captured the source-local namespace")

    def test_module_signature_cannot_construct_a_directive(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            module = self.module_bytes(
                "m",
                signatures=[["m.make", [], "directive"]],
            )
            write_bytes(directory / "m.json", module)
            records = [
                ["import", "m", sha256(module).hexdigest()],
                ["rule", "rule.test", ["m.make"], source_binding()],
            ]
            try:
                noema.compile_source(
                    noema._canonical_source(records),
                    directory,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )
            except noema.Refusal as raised:
                self.assertEqual(raised.code, "NOE-E-TYPE.SIGNATURE_RESULT")
            else:
                self.fail("module signature constructed a directive")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_linked_module_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "core.json").symlink_to(MODULES_FIXTURE / "core.json")
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(noema._canonical_source(base_records()), directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    def test_stale_build_lock_refuses(self):
        build, _artifacts = noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        build["lock"]["compiler_sha256"] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema._verify_build_value(build, MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.BUILD")

    def test_kernel_profile_mismatch_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            kernel = Path(temporary) / "kernel"
            kernel.write_text("different\n")
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, kernel)
            self.assertEqual(raised.exception.code, "NOE-E-DIGEST.KERNEL")

    def test_transitive_module_cap_accepts_exact_and_refuses_plus_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            digest = self._module_chain(directory, noema.MAX_IMPORTS)
            source = noema._canonical_source([["import", "m00", digest]])
            build, _artifacts = noema.compile_source(source, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual(len(build["graph"]["modules"]), noema.MAX_IMPORTS)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            digest = self._module_chain(directory, noema.MAX_IMPORTS + 1)
            source = noema._canonical_source([["import", "m00", digest]])
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(source, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.IMPORTS")

    def test_module_declarations_consume_the_graph_node_budget(self):
        exact_signatures = noema.MAX_GRAPH_NODES - 2
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            digest = self._signature_module(directory, exact_signatures)
            source = noema._canonical_source([["import", "m", digest]])
            noema.compile_source(source, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            digest = self._signature_module(directory, exact_signatures + 1)
            source = noema._canonical_source([["import", "m", digest]])
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(source, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.NODES")


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.build, self.artifacts = noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        self.profile = noema._decode_json(PROFILE_FIXTURE.read_bytes(), "profile", canonical=True)
        self.profile_digest = sha256(PROFILE_FIXTURE.read_bytes()).hexdigest()

    def test_projection_recovers_exact_graph(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        self.assertEqual(noema.recover_projection(bundle, self.profile), self.build["graph"])

    def test_projection_text_is_idempotent(self):
        first = noema.project_build(self.build, self.profile, self.profile_digest)
        second = noema.project_build(self.build, self.profile, self.profile_digest)
        self.assertEqual(noema._canonical_json(first), noema._canonical_json(second))

    def test_alias_collision_with_visible_literal_refuses(self):
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"][0][1] = "operator"
        with self.assertRaises(noema.Refusal) as raised:
            noema.project_build(self.build, profile, self.profile_digest)
        self.assertEqual(raised.exception.code, "NOE-E-ALIAS.COLLISION")

    def test_alias_collision_by_arity_still_refuses(self):
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"][1][1] = profile["aliases"][0][1]
        with self.assertRaises(noema.Refusal) as raised:
            noema.project_build(self.build, profile, self.profile_digest)
        self.assertEqual(raised.exception.code, "NOE-E-ALIAS.COLLISION")

    def test_alias_cannot_overload_predicate_and_literal_id(self):
        literal = ["literal", "core.ready", "text", "1", "x"]
        build, _artifacts = compile_records(base_records(literals=[literal]))
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"].insert(4, ["core.ready", "q"])
        profile_digest = sha256(noema._canonical_json(profile)).hexdigest()
        build["lock"]["profile_sha256"] = profile_digest
        with self.assertRaises(noema.Refusal) as raised:
            noema.project_build(build, profile, profile_digest)
        self.assertEqual(raised.exception.code, "NOE-E-ALIAS.OVERLOAD")

    def test_unused_alias_is_inert(self):
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"].append(["zz.absent", "Z"])
        profile_digest = sha256(noema._canonical_json(profile)).hexdigest()
        build = json.loads(json.dumps(self.build))
        build["lock"]["profile_sha256"] = profile_digest
        bundle = noema.project_build(build, profile, profile_digest)
        self.assertEqual(noema.recover_projection(bundle, profile), build["graph"])

    def test_tampered_projection_refuses(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        bundle["text"] = bundle["text"].replace("NT1", "NT0", 1)
        with self.assertRaises(noema.Refusal) as raised:
            noema.recover_projection(bundle, self.profile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.PROJECTION")

    def test_manifest_profile_mismatch_refuses(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        bundle["manifest"]["profile_sha256"] = "0" * 64
        bundle["lock"]["profile_sha256"] = "0" * 64
        bundle["manifest"]["lock_sha256"] = sha256(noema._canonical_json(bundle["lock"])).hexdigest()
        bundle["manifest"]["projection_sha256"] = sha256(bundle["text"].encode()).hexdigest()
        with self.assertRaises(noema.Refusal) as raised:
            noema.recover_projection(bundle, self.profile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.PROFILE")

    def test_manifest_lock_mismatch_refuses(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        bundle["manifest"]["lock_sha256"] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema.recover_projection(bundle, self.profile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.LOCK")

    def test_recovery_normalizes_malformed_alias_shape(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"] = [[]]
        profile_digest = sha256(noema._canonical_json(profile)).hexdigest()
        bundle["lock"]["profile_sha256"] = profile_digest
        bundle["manifest"]["profile_sha256"] = profile_digest
        bundle["manifest"]["aliases_sha256"] = sha256(noema._canonical_json(profile["aliases"])).hexdigest()
        bundle["manifest"]["lock_sha256"] = sha256(noema._canonical_json(bundle["lock"])).hexdigest()
        header, graph, _empty = bundle["text"].split("\n")
        _magic, _old_profile, graph_digest = header.split(" ")
        bundle["text"] = f"NT1 {profile_digest} {graph_digest}\n{graph}\n"
        bundle["manifest"]["projection_sha256"] = sha256(bundle["text"].encode()).hexdigest()
        with self.assertRaises(noema.Refusal) as raised:
            noema.recover_projection(bundle, profile)
        self.assertEqual(raised.exception.code, "NOE-E-ALIAS.SHAPE")


class SemanticDiffTests(unittest.TestCase):
    def setUp(self):
        self.build, _artifacts = noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)

    def test_noop_diff_has_no_entries(self):
        self.assertEqual(noema.semantic_diff(self.build, self.build)["entries"], [])

    def test_effect_change_is_named(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[4][2] = ["-", ["core.ready", [":", "state", "ready"]]]
        changed, _artifacts = compile_records(records)
        kinds = {entry["kind"] for entry in noema.semantic_diff(self.build, changed)["entries"]}
        self.assertIn("effect", kinds)

    def test_exception_subject_change_is_named_as_an_effect(self):
        exception = [
            "exception",
            "exception.test",
            [":", "actor", "alice"],
            ["=", [":", "state", "ready"], [":", "state", "ready"]],
            [":", "effect", "old"],
            [":", "scope", "repository"],
            [":", "evidence", "record"],
            [":", "value", "never"],
            ["-", [":", "effect", "recovery"]],
        ]
        records = base_records() + [exception]
        before, _artifacts = compile_records(records)
        changed_records = json.loads(json.dumps(records))
        changed_records[-1][4][2] = "new"
        after, _artifacts = compile_records(changed_records)
        kinds = {
            entry["kind"]
            for entry in noema.semantic_diff(before, after)["entries"]
        }
        self.assertIn("effect", kinds)

    def test_source_binding_change_is_named(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[4][3][4] = "9"
        changed, _artifacts = compile_records(records)
        kinds = {entry["kind"] for entry in noema.semantic_diff(self.build, changed)["entries"]}
        self.assertIn("source_binding", kinds)

    def test_literal_change_is_named(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[1][3:] = ["11", "git status!"]
        changed, _artifacts = compile_records(records)
        kinds = {entry["kind"] for entry in noema.semantic_diff(self.build, changed)["entries"]}
        self.assertIn("literal", kinds)

    def test_precedence_change_is_named(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[-1][3] = [":", "actor", "alternate"]
        changed, _artifacts = compile_records(records)
        kinds = {entry["kind"] for entry in noema.semantic_diff(self.build, changed)["entries"]}
        self.assertIn("authority", kinds)

    def test_diff_entries_are_closed_and_digest_bound(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[4][2] = ["-", ["core.ready", [":", "state", "ready"]]]
        changed, _artifacts = compile_records(records)
        diff = noema.semantic_diff(self.build, changed)
        for entry in diff["entries"]:
            self.assertEqual(set(entry), {"node", "kind", "change", "before", "after"})
            for digest in (entry["before"], entry["after"]):
                if digest is not None:
                    self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_maximum_precedence_node_fits_the_public_schema(self):
        high = "a" + "x" * 127
        low = "b" + "x" * 127
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", high, ["+", [":", "effect", "x"]], source_binding(0, 1)],
            ["rule", low, ["+", [":", "effect", "y"]], source_binding(1, 2)],
            [
                "precedence",
                high,
                low,
                [":", "actor", "x"],
                [":", "scope", "x"],
                [":", "evidence", "x"],
            ],
        ]
        before, _artifacts = compile_records(records)
        records[-1][3] = [":", "actor", "y"]
        after, _artifacts = compile_records(records)
        node = noema.semantic_diff(before, after)["entries"][0]["node"]
        maximum = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"][
            "diffEntry"
        ]["properties"]["node"]["maxLength"]
        self.assertEqual(len(node), 268)
        self.assertLessEqual(len(node), maximum)


class SliceTests(unittest.TestCase):
    def test_structurally_valid_forged_build_cannot_mint_a_sealed_manifest(self):
        effect = "forged.build"
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.deny",
                ["-", [":", "effect", effect]],
                source_binding(1, 2),
            ],
        ]
        build, artifacts = compile_records(records)
        forged = json.loads(json.dumps(build))
        forged["graph"]["records"] = [
            record
            for record in forged["graph"]["records"]
            if not (record[0] == "rule" and record[1] == "rule.deny")
        ]
        forged["lock"]["graph_sha256"] = noema._value_sha256(forged["graph"])
        profile = noema._decode_json(artifacts["profile"], "profile", canonical=True)
        with self.assertRaises(noema.Refusal) as raised:
            noema.select_runtime(
                forged,
                profile,
                sha256(artifacts["profile"]).hexdigest(),
                runtime_selection(effect),
            )
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.BUILD")

    def test_profile_value_must_match_the_locked_profile_digest(self):
        build, artifacts = compile_records(base_records())
        profile = noema._decode_json(artifacts["profile"], "profile", canonical=True)
        profile["tokenizer"] = "forged-tokenizer"
        with self.assertRaises(noema.Refusal) as raised:
            noema.select_runtime(
                build,
                profile,
                build["lock"]["profile_sha256"],
                runtime_selection("ready"),
            )
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.PROFILE")

    def test_checked_in_manifest_recomputes_exactly(self):
        manifest, projection = noema._verify_manifest_path(
            RUNTIME_FIXTURE / "manifest.json"
        )
        self.assertEqual(manifest["projection_sha256"], sha256(projection["text"].encode()).hexdigest())

    def test_same_inputs_return_identical_manifest_and_projection(self):
        _build, _selection, first_manifest, first_projection = runtime_fixture()
        _build, _selection, second_manifest, second_projection = runtime_fixture()
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(first_projection, second_projection)

    def test_included_and_omitted_ids_partition_selectable_graph(self):
        build, _selection, manifest, _projection = runtime_fixture()
        selectable = {
            noema._runtime_record_id(record)
            for record in build["graph"]["records"]
            if record[0] in noema.SELECTABLE_FORMS
        }
        omitted = {item["id"] for item in manifest["omitted"]}
        self.assertEqual(set(manifest["included_ids"]) | omitted, selectable)
        self.assertFalse(set(manifest["included_ids"]) & omitted)

    def test_primary_slice_closes_support_records_and_governance(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertTrue(
            {
                "promise.inspect",
                "handoff.inspect",
                "exception.deploy",
                "override.deploy",
                "precedence:rule.deploy.prohibit>rule.deploy.permit",
            }
            <= set(manifest["included_ids"])
        )

    def test_recovery_directive_survives_support_closure(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        promise = next(item for item in manifest["tape"] if item[0] == "promise")
        self.assertIn(["+", [":", "effect", "recover"]], promise)

    def test_macro_dependency_is_reachable(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertEqual(manifest["definitions"], ["local.operator_authorized"])

    def test_only_reachable_literals_enter_the_tape(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertEqual(manifest["literals"], ["lit.instruction", "lit.note"])
        self.assertNotIn("lit.unreachable", manifest["literals"])

    def test_unknown_guard_retains_its_rule(self):
        _build, _selection, manifest, _projection = runtime_fixture(
            "selection-unknown.json"
        )
        self.assertIn("rule.review", manifest["included_ids"])

    def test_checked_false_guard_carries_exact_proof(self):
        _build, selection, manifest, _projection = runtime_fixture(
            "selection-false.json"
        )
        omission = next(item for item in manifest["omitted"] if item["id"] == "rule.beta")
        self.assertEqual(omission["reason"], "checked-false-guard")
        self.assertEqual(omission["fact"], selection["facts"][0]["id"])
        self.assertEqual(omission["evidence_sha256"], selection["facts"][0]["evidence_sha256"])

    def test_changed_fact_changes_manifest_identity(self):
        build, selection, manifest, _projection = runtime_fixture("selection-false.json")
        changed = json.loads(json.dumps(selection))
        changed["facts"][0]["value"] = "true"
        profile = json.loads((RUNTIME_FIXTURE / "profile.json").read_text())
        other, _projection = noema.select_runtime(
            build,
            profile,
            build["lock"]["profile_sha256"],
            changed,
        )
        self.assertNotEqual(noema._value_sha256(manifest), noema._value_sha256(other))

    def test_changed_operation_changes_manifest_identity(self):
        build, selection, manifest, _projection = runtime_fixture()
        changed = dict(selection)
        changed["operation"] = "review"
        profile = json.loads((RUNTIME_FIXTURE / "profile.json").read_text())
        other, _projection = noema.select_runtime(
            build,
            profile,
            build["lock"]["profile_sha256"],
            changed,
        )
        self.assertNotEqual(manifest["selection_sha256"], other["selection_sha256"])

    def test_manifest_tape_digest_is_exact(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertEqual(manifest["tape_sha256"], noema._value_sha256(manifest["tape"]))

    def test_slice_projection_recovers_exact_tape(self):
        _build, _selection, manifest, projection = runtime_fixture()
        profile = json.loads((RUNTIME_FIXTURE / "profile.json").read_text())
        self.assertEqual(noema._validate_slice_projection(projection, manifest, profile), projection)

    def test_omission_evidence_mismatch_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture("selection-false.json")
        hostile = json.loads(json.dumps(manifest))
        omission = next(item for item in hostile["omitted"] if item["id"] == "rule.beta")
        omission["evidence_sha256"] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_manifest_value(hostile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.OMISSION")

    def test_tape_digest_mismatch_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        hostile = json.loads(json.dumps(manifest))
        hostile["tape_sha256"] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_manifest_value(hostile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.TAPE")

    def test_unsorted_facts_refuse(self):
        _build, selection, _manifest, _projection = runtime_fixture()
        hostile = json.loads(json.dumps(selection))
        hostile["facts"] = list(reversed(hostile["facts"]))
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_selection(hostile)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_arbitrary_fact_identity_refuses(self):
        fact = {"id": "fact.claimed", "value": "true", "evidence_sha256": "0" * 64}
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_facts([fact], "facts")
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.FACT_ID")

    def test_artifact_path_escape_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        hostile = json.loads(json.dumps(manifest))
        hostile["artifacts"]["build"] = "../build.json"
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_manifest_value(hostile)
        self.assertEqual(raised.exception.code, "NOE-E-PATH.LEAF")

    def test_stale_selection_artifact_refuses_manifest_verification(self):
        with scratch_directory("noema-runtime-stale-") as temporary:
            root = Path(temporary)
            (root / "modules").mkdir()
            for name in ("build.json", "profile.json", "kernel.noe", "projection.json", "manifest.json"):
                write_bytes(root / name, (RUNTIME_FIXTURE / name).read_bytes())
            write_bytes(root / "modules" / "core.json", (RUNTIME_FIXTURE / "modules" / "core.json").read_bytes())
            selection = json.loads((RUNTIME_FIXTURE / "selection.json").read_text())
            selection["operation"] = "review"
            write_bytes(root / "selection.json", noema._canonical_json(selection))
            with self.assertRaises(noema.Refusal) as raised:
                noema._verify_manifest_path(root / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MANIFEST")

    def test_absent_root_falls_back_to_full_conservative_slice(self):
        records = base_records(["+", [":", "effect", "known"]])
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("absent", target="nowhere"),
        )
        self.assertEqual(manifest["included_ids"], ["rule.test"])

    def test_macro_hidden_prohibition_remains_reachable(self):
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "definition",
                "local.hidden_prohibition",
                [],
                [
                    "core.authorized",
                    [":", "actor", "admin"],
                    [":", "effect", "hidden"],
                ],
            ],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", "hidden"]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.deny",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["-", ["local.hidden_prohibition"]],
                ],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("hidden"),
        )
        self.assertIn("rule.deny", manifest["included_ids"])
        result = noema.check_runtime("hidden", [], manifest)
        self.assertEqual(result["output"]["reason"], "prohibition")

    def test_composite_guard_needs_one_exact_fact_before_omission(self):
        first = ["core.checked", [":", "evidence", "guard.first"]]
        second = ["core.checked", [":", "evidence", "guard.second"]]
        facts = sorted(
            (
                checked_fact(first, "false", "guard-first"),
                checked_fact(second, "false", "guard-second"),
            ),
            key=lambda item: item["id"],
        )
        _build, manifest, _projection = select_records(
            base_records(
                ["?", ["|", first, second], ["+", [":", "effect", "guarded"]]]
            ),
            runtime_selection("guarded", facts=facts),
        )
        self.assertIn("rule.test", manifest["included_ids"])


class PolicyCheckTests(unittest.TestCase):
    def test_allowed_consequence_zero_case_permits(self):
        _build, selection, manifest, _projection = runtime_fixture()
        result = noema.check_runtime("inspect", selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_consequence_three_prohibition_refuses(self):
        _build, selection, manifest, _projection = runtime_fixture(
            "selection-deploy.json"
        )
        result = noema.check_runtime("deploy", selection["facts"], manifest)
        self.assertEqual((result["output"]["decision"], result["output"]["consequence"]), ("refuse", 3))

    def test_unknown_guard_returns_unknown(self):
        _build, selection, manifest, _projection = runtime_fixture(
            "selection-unknown.json"
        )
        result = noema.check_runtime("review", selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "unknown")

    def test_permission_never_cancels_prohibition(self):
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.allow", ["+", [":", "effect", "conflict"]], source_binding(0, 1)],
            ["rule", "rule.deny", ["-", [":", "effect", "conflict"]], source_binding(1, 2)],
        ]
        _build, manifest, _projection = select_records(records, runtime_selection("conflict"))
        result = noema.check_runtime("conflict", [], manifest)
        self.assertEqual((result["output"]["decision"], result["output"]["reason"]), ("refuse", "prohibition"))

    def test_missing_policy_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture("selection-unknown.json")
        result = noema.check_runtime("absent", [], manifest)
        self.assertEqual(result["output"]["reason"], "no-applicable-policy")

    def test_fact_set_must_match_manifest(self):
        _build, selection, manifest, _projection = runtime_fixture()
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime("inspect", selection["facts"][:-1], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.FACTS")

    def test_scope_mismatch_keeps_high_consequence_default_deny(self):
        consequence = [":", "core.consequence", "3"]
        directive = [
            "@",
            [":", "scope", "other"],
            ["^", [":", "actor", "operator"], [";", ["!", ["=", consequence, consequence]], ["+", [":", "effect", "scoped"]]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection("scoped", authority=("operator",)),
        )
        result = noema.check_runtime("scoped", [], manifest)
        self.assertEqual(result["output"]["reason"], "default-deny")

    def test_inactive_nested_low_consequence_permission_does_not_default_permit(self):
        gate = ["core.checked", [":", "evidence", "disabled"]]
        fact = checked_fact(gate, "false", "disabled")
        consequence = [":", "core.consequence", "0"]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", gate, ["+", [":", "effect", "inactive.low"]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection("inactive.low", facts=(fact,)),
        )
        result = noema.check_runtime("inactive.low", [fact], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "no-applicable-policy"),
        )

    def test_out_of_scope_low_consequence_permission_does_not_default_permit(self):
        consequence = [":", "core.consequence", "0"]
        directive = [
            "@",
            [":", "scope", "other"],
            [
                ";",
                ["!", ["=", consequence, consequence]],
                ["+", [":", "effect", "scoped.low"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection("scoped.low", target="repository"),
        )
        result = noema.check_runtime("scoped.low", [], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "no-applicable-policy"),
        )

    def test_nested_authority_wrappers_accumulate(self):
        consequence = [":", "core.consequence", "3"]
        directive = [
            "^",
            [":", "actor", "outer"],
            [
                "^",
                [":", "actor", "inner"],
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", "nested.authority"]],
                ],
            ],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection("nested.authority", authority=("inner",)),
        )
        result = noema.check_runtime("nested.authority", [], manifest)
        self.assertEqual(result["output"]["decision"], "refuse")

    def test_nested_scope_wrappers_accumulate(self):
        consequence = [":", "core.consequence", "3"]
        directive = [
            "^",
            [":", "actor", "operator"],
            [
                "@",
                [":", "scope", "other"],
                [
                    "@",
                    [":", "scope", "repository"],
                    [
                        ";",
                        ["!", ["=", consequence, consequence]],
                        ["+", [":", "effect", "nested.scope"]],
                    ],
                ],
            ],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(
                "nested.scope",
                target="repository",
                authority=("operator",),
            ),
        )
        result = noema.check_runtime("nested.scope", [], manifest)
        self.assertEqual(result["output"]["decision"], "refuse")

    def test_all_nested_authorities_and_scopes_can_apply_together(self):
        consequence = [":", "core.consequence", "3"]
        directive = [
            "^",
            [":", "actor", "outer"],
            [
                "^",
                [":", "actor", "inner"],
                [
                    "@",
                    [":", "scope", "repository"],
                    [
                        "@",
                        [":", "scope", "target"],
                        [
                            ";",
                            ["!", ["=", consequence, consequence]],
                            ["+", [":", "effect", "nested.all"]],
                        ],
                    ],
                ],
            ],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(
                "nested.all",
                target="target",
                authority=("inner", "outer"),
            ),
        )
        result = noema.check_runtime("nested.all", [], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_authority_wrapper_mismatch_refuses(self):
        directive = ["^", [":", "actor", "admin"], ["+", [":", "effect", "owned"]]]
        _build, manifest, _projection = select_records(
            base_records(directive), runtime_selection("owned", authority=("operator",))
        )
        result = noema.check_runtime("owned", [], manifest)
        self.assertEqual(result["output"]["reason"], "authority-mismatch")

    def test_false_requirement_refuses(self):
        proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", "required"]]
        fact = checked_fact(proposition, "false", "required-false")
        directive = [";", ["!", proposition], ["+", [":", "effect", "required"]]]
        _build, manifest, _projection = select_records(
            base_records(directive), runtime_selection("required", facts=(fact,))
        )
        result = noema.check_runtime("required", [fact], manifest)
        self.assertEqual(result["output"]["reason"], "failed-requirement")

    def test_opposed_requirements_need_typed_override(self):
        proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", "opposed"]]
        consequence = [":", "core.consequence", "0"]
        fact = checked_fact(proposition, "true", "opposed")
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.high", [";", ["!", ["=", consequence, consequence]], ["!", proposition]], source_binding(0, 1)],
            ["rule", "rule.low", [";", ["!", ["=", consequence, consequence]], ["!", ["~", proposition]]], source_binding(1, 2)],
        ]
        _build, manifest, _projection = select_records(records, runtime_selection("opposed", facts=(fact,)))
        result = noema.check_runtime("opposed", [fact], manifest)
        self.assertEqual(result["output"]["reason"], "conflicting-requirements")

    def test_checked_higher_authority_override_resolves_requirements(self):
        proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", "opposed"]]
        consequence = [":", "core.consequence", "0"]
        evidence = [":", "evidence", "override"]
        facts = (
            checked_fact(proposition, "true", "opposed"),
            checked_fact(["core.checked", evidence], "true", "override"),
        )
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.high", [";", ["!", ["=", consequence, consequence]], ["!", proposition]], source_binding(0, 1)],
            ["rule", "rule.low", [";", ["!", ["=", consequence, consequence]], ["!", ["~", proposition]]], source_binding(1, 2)],
            ["override", "override.opposed", [":", "actor", "admin"], "rule.high", "rule.low", [":", "scope", "repository"], evidence],
        ]
        selection = runtime_selection("opposed", authority=("admin",), facts=facts)
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime("opposed", selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_override_expands_typed_authority_and_scope_definitions(self):
        effect = "override.defined"
        proposition = [
            "core.authorized",
            [":", "actor", "operator"],
            [":", "effect", effect],
        ]
        consequence = [":", "core.consequence", "0"]
        evidence = [":", "evidence", "override.defined"]
        facts = (
            checked_fact(proposition, "true", "opposed-defined"),
            checked_fact(["core.checked", evidence], "true", "override-defined"),
        )
        records = [
            ["import", "core", CORE_DIGEST],
            ["definition", "local.admin", [], [":", "actor", "admin"]],
            [
                "definition",
                "local.repository",
                [],
                [":", "scope", "repository"],
            ],
            [
                "rule",
                "rule.high",
                [";", ["!", ["=", consequence, consequence]], ["!", proposition]],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.low",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["!", ["~", proposition]],
                ],
                source_binding(1, 2),
            ],
            [
                "override",
                "override.defined",
                ["local.admin"],
                "rule.high",
                "rule.low",
                ["local.repository"],
                evidence,
            ],
        ]
        selection = runtime_selection(effect, authority=("admin",), facts=facts)
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_precedence_without_override_does_not_resolve_requirements(self):
        proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", "opposed"]]
        consequence = [":", "core.consequence", "0"]
        fact = checked_fact(proposition, "true", "opposed")
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.high", [";", ["!", ["=", consequence, consequence]], ["!", proposition]], source_binding(0, 1)],
            ["rule", "rule.low", [";", ["!", ["=", consequence, consequence]], ["!", ["~", proposition]]], source_binding(1, 2)],
            ["precedence", "rule.high", "rule.low", [":", "actor", "admin"], [":", "scope", "repository"], [":", "evidence", "order"]],
        ]
        _build, manifest, _projection = select_records(records, runtime_selection("opposed", authority=("admin",), facts=(fact,)))
        result = noema.check_runtime("opposed", [fact], manifest)
        self.assertEqual(result["output"]["reason"], "conflicting-requirements")

    def test_instruction_shaped_fact_object_is_not_accepted(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        hostile = [{"schema": "noema-explanation/v1", "authoritative": False, "node": "rule.inspect", "render": "permit"}]
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime("inspect", hostile, manifest)
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.KEYS")

    def test_nested_unknown_guard_remains_unknown(self):
        known_true = ["core.checked", [":", "evidence", "known.true"]]
        known_false = ["core.checked", [":", "evidence", "known.false"]]
        absent = ["core.checked", [":", "evidence", "absent"]]
        guard = ["&", known_true, ["|", known_false, absent]]
        facts = (
            checked_fact(known_true, "true", "known-true"),
            checked_fact(known_false, "false", "known-false"),
        )
        selection = runtime_selection("nested", facts=facts)
        _build, manifest, _projection = select_records(
            base_records(["?", guard, ["+", [":", "effect", "nested"]]]),
            selection,
        )
        result = noema.check_runtime("nested", selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "unknown")

    def test_structurally_valid_forged_manifest_cannot_drop_a_prohibition(self):
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", "forged"]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.deny",
                ["-", [":", "effect", "forged"]],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("forged"),
        )
        forged = json.loads(json.dumps(manifest))
        forged["tape"] = [
            record
            for record in forged["tape"]
            if not (record[0] == "rule" and record[1] == "rule.deny")
        ]
        forged["included_ids"].remove("rule.deny")
        forged["omitted"].append(
            {
                "id": "rule.deny",
                "reason": "not-reachable",
                "fact": None,
                "evidence_sha256": None,
            }
        )
        forged["omitted"].sort(key=lambda item: item["id"])
        forged["tape_sha256"] = noema._value_sha256(forged["tape"])
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime("forged", [], forged)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MANIFEST")

    def test_selected_manifest_mutation_invalidates_its_runtime_seal(self):
        _build, manifest, _projection = select_records(
            base_records(["+", [":", "effect", "sealed"]]),
            runtime_selection("sealed"),
        )
        manifest["selection"]["target"] = "other"
        manifest["selection_sha256"] = noema._value_sha256(manifest["selection"])
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime("sealed", [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MANIFEST")

    def test_inactive_high_requirement_cannot_override_an_active_failure(self):
        effect = "override.bypass"
        proposition = [
            "core.authorized",
            [":", "actor", "operator"],
            [":", "effect", effect],
        ]
        disabled = ["core.checked", [":", "evidence", "high.disabled"]]
        override_evidence = [":", "evidence", "override.checked"]
        consequence = [":", "core.consequence", "0"]
        facts = sorted(
            (
                checked_fact(proposition, "false", "requirement-false"),
                checked_fact(disabled, "false", "high-disabled"),
                checked_fact(
                    ["core.checked", override_evidence],
                    "true",
                    "override-checked",
                ),
            ),
            key=lambda item: item["id"],
        )
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.high",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["?", disabled, ["!", ["~", proposition]]],
                ],
                source_binding(1, 2),
            ],
            [
                "rule",
                "rule.low",
                [";", ["!", ["=", consequence, consequence]], ["!", proposition]],
                source_binding(2, 3),
            ],
            [
                "override",
                "override.bypass",
                [":", "actor", "admin"],
                "rule.high",
                "rule.low",
                [":", "scope", "repository"],
                override_evidence,
            ],
        ]
        selection = runtime_selection(
            effect,
            authority=("admin",),
            facts=facts,
        )
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "failed-requirement"),
        )

    def test_expired_exception_refuses_beside_a_low_consequence_permission(self):
        effect = "exception.bypass"
        evidence = [":", "evidence", "exception.checked"]
        gate = ["core.checked", evidence]
        fact = checked_fact(gate, "true", "exception-checked")
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "exception",
                "exception.expired",
                [":", "actor", "admin"],
                gate,
                [":", "effect", effect],
                [":", "scope", "repository"],
                evidence,
                [":", "value", "expired"],
                ["+", [":", "effect", "recover"]],
            ],
        ]
        selection = runtime_selection(
            effect,
            authority=("admin",),
            facts=(fact,),
        )
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "invalid-exception"),
        )

    def test_valid_exception_cannot_mint_permission(self):
        effect = "exception.valid"
        evidence = [":", "evidence", "exception.valid"]
        gate = ["core.checked", evidence]
        fact = checked_fact(gate, "true", "exception-valid")
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "exception",
                "exception.valid",
                [":", "actor", "admin"],
                gate,
                [":", "effect", effect],
                [":", "scope", "repository"],
                evidence,
                [":", "value", "active"],
                ["+", [":", "effect", "recover"]],
            ],
        ]
        selection = runtime_selection(effect, authority=("admin",), facts=(fact,))
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "no-applicable-policy"),
        )

    def test_exception_expands_typed_field_definitions(self):
        effect = "exception.defined"
        evidence = [":", "evidence", "exception.defined"]
        gate = ["core.checked", evidence]
        fact = checked_fact(gate, "true", "exception-defined")
        records = [
            ["import", "core", CORE_DIGEST],
            ["definition", "local.active", [], [":", "value", "active"]],
            ["definition", "local.admin", [], [":", "actor", "admin"]],
            [
                "definition",
                "local.repository",
                [],
                [":", "scope", "repository"],
            ],
            [
                "exception",
                "exception.defined",
                ["local.admin"],
                gate,
                [":", "effect", effect],
                ["local.repository"],
                evidence,
                ["local.active"],
                ["+", [":", "effect", "recover"]],
            ],
        ]
        selection = runtime_selection(effect, authority=("admin",), facts=(fact,))
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(result["output"]["reason"], "no-applicable-policy")

    def test_missing_consequence_marker_is_not_masked_by_an_explicit_zero(self):
        effect = "mixed.consequence"
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.explicit",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.missing",
                ["+", [":", "effect", effect]],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(effect),
        )
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.CONSEQUENCE")

    def test_out_of_range_consequence_marker_refuses(self):
        effect = "invalid.consequence"
        consequence = [":", "core.consequence", "4"]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["+", [":", "effect", effect]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect, authority=("operator",)),
        )
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.CONSEQUENCE")

    def test_requirement_pair_work_has_a_closed_runtime_budget(self):
        effect = "policy.budget"
        records = [["import", "core", CORE_DIGEST]]
        for index in range(4):
            records.append(
                [
                    "rule",
                    f"rule.budget.{index}",
                    [
                        "!",
                        [
                            "core.authorized",
                            [":", "actor", f"actor.{index}"],
                            [":", "effect", effect],
                        ],
                    ],
                    source_binding(index, index + 1),
                ]
            )
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(effect),
        )
        with mock.patch.object(noema, "MAX_POLICY_PAIRS", 4, create=True):
            with self.assertRaises(noema.Refusal) as raised:
                noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.POLICY")

    def test_quantified_truth_shares_one_expansion_budget(self):
        effect = "truth.budget"
        consequence = [":", "core.consequence", "0"]
        members = [
            [":", "actor", "actor.five"],
            [":", "actor", "actor.four"],
            [":", "actor", "actor.one"],
            [":", "actor", "actor.three"],
            [":", "actor", "actor.two"],
        ]
        proposition = [
            "all",
            ["item", "actor"],
            ["{}", "actor", *members],
            ["=", ["%", "item"], ["%", "item"]],
        ]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", proposition, ["+", [":", "effect", effect]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect),
        )
        with mock.patch.object(
            noema,
            "MAX_TRUTH_EXPANSION_NODES",
            45,
            create=True,
        ):
            with self.assertRaises(noema.Refusal) as raised:
                noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.EXPANSION")

    def test_requirement_alone_never_permits_an_effect(self):
        proposition = [
            "core.authorized",
            [":", "actor", "operator"],
            [":", "effect", "require.only"],
        ]
        fact = checked_fact(proposition, "true", "require-only")
        directive = [
            "^",
            [":", "actor", "operator"],
            ["!", proposition],
        ]
        selection = runtime_selection(
            "require.only",
            authority=("operator",),
            facts=(fact,),
        )
        _build, manifest, _projection = select_records(
            base_records(directive),
            selection,
        )
        result = noema.check_runtime("require.only", selection["facts"], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "default-deny"),
        )

    def test_closed_truth_refuses_a_contradictory_checked_fact(self):
        proposition = [
            "=",
            [":", "effect", "fact.bypass"],
            [":", "effect", "fact.bypass"],
        ]
        fact = checked_fact(proposition, "false", "contradictory")
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", "fact.bypass"]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.deny",
                ["?", proposition, ["-", [":", "effect", "fact.bypass"]]],
                source_binding(1, 2),
            ],
        ]
        with self.assertRaises(noema.Refusal) as raised:
            select_records(
                records,
                runtime_selection("fact.bypass", facts=(fact,)),
            )
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.FACT_CONFLICT")


class TransitionTests(unittest.TestCase):
    def test_transition_expands_its_typed_state_definition(self):
        gate = ["=", [":", "state", "idle"], [":", "state", "idle"]]
        records = [
            ["import", "core", CORE_DIGEST],
            ["definition", "local.ready", [], [":", "state", "ready"]],
            [
                "rule",
                "rule.move",
                ["+", [":", "effect", "move"]],
                source_binding(0, 1),
            ],
            [
                "transition",
                "transition.defined",
                [":", "state", "machine"],
                [":", "state", "idle"],
                [":", "event", "go"],
                gate,
                ["local.ready"],
                ["+", [":", "effect", "move"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("move", state="idle"),
        )
        result = noema.next_runtime("machine", "idle", "go", [], manifest)
        self.assertEqual(result["output"]["next_state"], "ready")

    def test_established_transition_returns_ordered_effects(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        receipts = noema._read_fact_array(RUNTIME_FIXTURE / "receipts.json", "receipts")
        result = noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        self.assertEqual(result["output"]["status"], "transition")
        self.assertEqual([item[1][2] for item in result["output"]["effects"]], ["inspect", "record"])

    def test_wrong_event_stops(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.next_runtime("workflow", "idle", "other", [], manifest)
        self.assertEqual((result["output"]["status"], result["output"]["reason"]), ("stop", "no-enabled-transition"))

    def test_wrong_machine_stops(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.next_runtime("other", "idle", "requested", [], manifest)
        self.assertEqual(result["output"]["controlling_node"], "default.stop")

    def test_wrong_state_stops(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.next_runtime("workflow", "ready", "requested", [], manifest)
        self.assertEqual(result["output"]["next_state"], None)

    def test_unknown_transition_guard_stops_unknown(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.next_runtime("workflow", "idle", "requested", [], manifest)
        self.assertEqual((result["verdict"], result["output"]["reason"]), ("unknown", "unestablished-guard"))

    def test_false_transition_guard_stops(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        proposition = ["core.checked", [":", "evidence", "receipt"]]
        receipt = checked_fact(proposition, "false", "receipt-false")
        result = noema.next_runtime("workflow", "idle", "requested", [receipt], manifest)
        self.assertEqual(result["output"]["reason"], "no-enabled-transition")

    def test_contradictory_receipt_refuses(self):
        build, selection, manifest, projection = runtime_fixture()
        proposition = ["core.ready", [":", "state", "idle"]]
        conflict = checked_fact(proposition, "false", "different-evidence")
        conflict["id"] = selection["facts"][0]["id"]
        with self.assertRaises(noema.Refusal) as raised:
            noema.next_runtime("workflow", "idle", "requested", [conflict], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.FACTS")

    def test_multiple_enabled_transitions_refuse(self):
        gate = ["=", [":", "state", "idle"], [":", "state", "idle"]]
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.move", ["+", [":", "effect", "move"]], source_binding(0, 1)],
            ["transition", "transition.a", [":", "state", "machine"], [":", "state", "idle"], [":", "event", "go"], gate, [":", "state", "state.one"], ["+", [":", "effect", "step.one"]]],
            ["transition", "transition.b", [":", "state", "machine"], [":", "state", "idle"], [":", "event", "go"], gate, [":", "state", "state.two"], ["+", [":", "effect", "step.two"]]],
        ]
        _build, manifest, _projection = select_records(records, runtime_selection("move", state="idle"))
        with self.assertRaises(noema.Refusal) as raised:
            noema.next_runtime("machine", "idle", "go", [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.TRANSITION")

    def test_established_transition_stops_for_an_unknown_competitor(self):
        established = ["=", [":", "state", "idle"], [":", "state", "idle"]]
        unknown = ["core.checked", [":", "evidence", "transition.maybe"]]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.move",
                ["+", [":", "effect", "move"]],
                source_binding(0, 1),
            ],
            [
                "transition",
                "transition.established",
                [":", "state", "machine"],
                [":", "state", "idle"],
                [":", "event", "go"],
                established,
                [":", "state", "state.one"],
                ["+", [":", "effect", "step.one"]],
            ],
            [
                "transition",
                "transition.unknown",
                [":", "state", "machine"],
                [":", "state", "idle"],
                [":", "event", "go"],
                unknown,
                [":", "state", "state.two"],
                ["+", [":", "effect", "step.two"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("move", state="idle"),
        )
        result = noema.next_runtime("machine", "idle", "go", [], manifest)
        self.assertEqual(
            (result["output"]["status"], result["output"]["reason"]),
            ("stop", "unestablished-guard"),
        )

    def test_receipts_must_be_sorted(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        first = checked_fact(["core.ready", [":", "state", "x"]], label="x")
        second = checked_fact(["core.ready", [":", "state", "y"]], label="y")
        receipts = sorted([first, second], key=lambda item: item["id"], reverse=True)
        with self.assertRaises(noema.Refusal) as raised:
            noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_transition_is_deterministic(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        receipts = noema._read_fact_array(RUNTIME_FIXTURE / "receipts.json", "receipts")
        first = noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        second = noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        self.assertEqual(first, second)

    def test_transition_does_not_execute_instruction_literal(self):
        marker = Path("/tmp/noema-owned")
        marker.unlink(missing_ok=True)
        _build, _selection, manifest, _projection = runtime_fixture()
        receipts = noema._read_fact_array(RUNTIME_FIXTURE / "receipts.json", "receipts")
        noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        self.assertFalse(marker.exists())


class LiteralTests(unittest.TestCase):
    def test_reachable_literal_returns_exact_bytes(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.literal_runtime("lit.instruction", manifest)
        self.assertEqual(result["output"]["value"], "$(touch /tmp/noema-owned)")

    def test_reachable_literal_retains_kind(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.literal_runtime("lit.instruction", manifest)
        self.assertEqual(result["output"]["kind"], "command")

    def test_literal_digest_covers_exact_utf8(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.literal_runtime("lit.note", manifest)
        self.assertEqual(result["output"]["sha256"], sha256(b"inspect only").hexdigest())

    def test_unreachable_literal_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        with self.assertRaises(noema.Refusal) as raised:
            noema.literal_runtime("lit.unreachable", manifest)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.LITERAL")

    def test_literal_is_inert_even_when_command_shaped(self):
        marker = Path("/tmp/noema-owned")
        marker.unlink(missing_ok=True)
        _build, _selection, manifest, _projection = runtime_fixture()
        noema.literal_runtime("lit.instruction", manifest)
        self.assertFalse(marker.exists())

    def test_malformed_literal_id_refuses_without_echo(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        with self.assertRaises(noema.Refusal) as raised:
            noema.literal_runtime("$(touch bad)", manifest)
        self.assertEqual(raised.exception.field, "literal")
        self.assertNotIn("touch", raised.exception.message)

    def test_literal_inventory_drift_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        hostile = json.loads(json.dumps(manifest))
        hostile["literals"] = []
        with self.assertRaises(noema.Refusal) as raised:
            noema.literal_runtime("lit.instruction", hostile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.TAPE")


class ExplainTests(unittest.TestCase):
    def test_explanation_is_explicitly_non_authoritative(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.explain_runtime("rule.inspect", manifest)
        self.assertEqual((result["code"], result["output"]["authoritative"]), ("NOE-I-NON_AUTHORITATIVE", False))

    def test_explanation_render_is_canonical_record_json(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.explain_runtime("rule.inspect", manifest)
        record = next(item for item in manifest["tape"] if item[0] == "rule" and item[1] == "rule.inspect")
        self.assertEqual(result["output"]["render"], noema._canonical_json(record).decode().rstrip("\n"))

    def test_missing_node_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        with self.assertRaises(noema.Refusal) as raised:
            noema.explain_runtime("rule.absent", manifest)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.NODE")

    def test_precedence_node_can_be_explained(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        node = "precedence:rule.deploy.prohibit>rule.deploy.permit"
        result = noema.explain_runtime(node, manifest)
        self.assertEqual(result["output"]["node"], node)

    def test_explanation_cannot_be_consumed_as_facts(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        explanation = noema.explain_runtime("rule.inspect", manifest)["output"]
        with self.assertRaises(noema.Refusal):
            noema.check_runtime("inspect", [explanation], manifest)

    def test_explanation_cannot_be_consumed_as_manifest(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        explanation = noema.explain_runtime("rule.inspect", manifest)["output"]
        with self.assertRaises(noema.Refusal) as raised:
            noema.explain_runtime("rule.inspect", explanation)
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.KEYS")

    def test_explanation_is_deterministic(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertEqual(
            noema.explain_runtime("rule.inspect", manifest),
            noema.explain_runtime("rule.inspect", manifest),
        )


class RuntimeResultTests(unittest.TestCase):
    def run_main(self, arguments):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = noema.main(arguments)
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return status, json.loads(lines[0])

    def test_runtime_self_test_cli_passes(self):
        status, result = self.run_main(["runtime-self-test"])
        self.assertEqual((status, result["counts"]["cases"]), (0, 7))

    def test_manifest_verify_cli_passes(self):
        status, result = self.run_main(["verify", "--manifest", str(RUNTIME_FIXTURE / "manifest.json")])
        self.assertEqual((status, result["verdict"]), (0, "ok"))

    def test_check_cli_returns_policy_data(self):
        status, result = self.run_main([
            "check", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--effect", "inspect", "--facts", str(RUNTIME_FIXTURE / "facts.json"),
        ])
        self.assertEqual((status, result["output"]["decision"]), (0, "permit"))

    def test_next_cli_returns_ordered_data(self):
        status, result = self.run_main([
            "next", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--machine", "workflow", "--state", "idle", "--event", "requested",
            "--receipts", str(RUNTIME_FIXTURE / "receipts.json"),
        ])
        self.assertEqual((status, len(result["output"]["effects"])), (0, 2))

    def test_literal_cli_returns_data(self):
        status, result = self.run_main([
            "literal", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--id", "lit.note",
        ])
        self.assertEqual((status, result["output"]["value"]), (0, "inspect only"))

    def test_explain_cli_labels_render(self):
        status, result = self.run_main([
            "explain", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--node", "rule.inspect",
        ])
        self.assertEqual((status, result["output"]["authoritative"]), (0, False))

    def test_runtime_commands_expose_no_output_path(self):
        help_actions = {
            action.dest
            for action in noema.parser()._subparsers._group_actions[0].choices["check"]._actions
        }
        self.assertNotIn("output", help_actions)

    def test_policy_refusal_is_a_successful_command_result(self):
        _build, selection, manifest, _projection = runtime_fixture("selection-deploy.json")
        result = noema.check_runtime("deploy", selection["facts"], manifest)
        self.assertEqual((result["verdict"], result["code"]), ("refuse", "NOE-I-POLICY_REFUSE"))

    def test_unknown_is_distinct_from_refusal(self):
        _build, selection, manifest, _projection = runtime_fixture("selection-unknown.json")
        result = noema.check_runtime("review", selection["facts"], manifest)
        self.assertEqual((result["verdict"], result["code"]), ("unknown", "NOE-I-POLICY_UNKNOWN"))

    def test_every_runtime_result_has_bounded_correlation(self):
        _build, selection, manifest, _projection = runtime_fixture()
        results = [
            noema.check_runtime("inspect", selection["facts"], manifest),
            noema.next_runtime("workflow", "idle", "other", [], manifest),
            noema.literal_runtime("lit.note", manifest),
            noema.explain_runtime("rule.inspect", manifest),
        ]
        for result in results:
            with self.subTest(command=result["command"]):
                self.assertRegex(result["correlation_id"], r"^[0-9a-f]{64}$")
                self.assertLessEqual(len(result["message"]), 512)

    def test_invalid_effect_is_redacted(self):
        status, result = self.run_main([
            "check", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--effect", "$(touch /tmp/noema-bad)", "--facts", str(RUNTIME_FIXTURE / "facts.json"),
        ])
        self.assertEqual(status, 2)
        self.assertNotIn("touch", result["message"])

    def test_result_schema_closes_runtime_output(self):
        definitions = json.loads(SCHEMA.read_text())["$defs"]
        self.assertEqual(
            {item["$ref"].rsplit("/", 1)[-1] for item in definitions["runtimeOutput"]["oneOf"]},
            {"selectOutput", "checkOutput", "nextOutput", "literalOutput", "explainOutput"},
        )
        for name in ("selectOutput", "checkOutput", "nextOutput", "literalOutput", "explainOutput"):
            self.assertFalse(definitions[name]["additionalProperties"])


class PathBoundaryTests(unittest.TestCase):
    def test_non_scalar_output_leaf_refuses_through_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = str(Path(temporary) / "output") + "\udcff"
            arguments = [
                "parse",
                "--source",
                str(CODEC_FIXTURE),
                "--modules",
                str(MODULES_FIXTURE),
                "--profile",
                str(PROFILE_FIXTURE),
                "--kernel",
                str(KERNEL_FIXTURE),
                "--output",
                output,
            ]
            stdout = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout):
                    status = noema.main(arguments)
            except UnicodeEncodeError:
                self.fail("non-scalar output leaf escaped the refusal channel")
            self.assertEqual(status, 2)
            lines = stdout.getvalue().splitlines()
            self.assertEqual(len(lines), 1)
            result = json.loads(lines[0])
            self.assertEqual(result["code"], "NOE-E-PATH.LEAF")
            self.assertEqual(result["field"], "output")
            self.assertEqual(list(Path(temporary).iterdir()), [])

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_linked_input_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            link = Path(temporary) / "source.noe"
            link.symlink_to(CODEC_FIXTURE)
            with self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(link, "source", noema.MAX_INPUT_BYTES)
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    def test_directory_input_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(Path(temporary), "source", noema.MAX_INPUT_BYTES)
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs are unavailable")
    def test_fifo_input_refuses_without_opening(self):
        with tempfile.TemporaryDirectory() as temporary:
            fifo = Path(temporary) / "pipe"
            os.mkfifo(fifo)
            with self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(fifo, "source", noema.MAX_INPUT_BYTES)
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_linked_output_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "target"
            target.write_text("old")
            link = directory / "link"
            link.symlink_to(target)
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(link, b"new")
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")
            self.assertEqual(target.read_text(), "old")

    def test_directory_output_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(Path(temporary), b"new")
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs are unavailable")
    def test_fifo_output_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            fifo = Path(temporary) / "pipe"
            os.mkfifo(fifo)
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(fifo, b"new")
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    def test_partial_writes_are_completed(self):
        real_write = os.write
        calls = 0

        def partial(descriptor, payload):
            nonlocal calls
            calls += 1
            return real_write(descriptor, payload[: max(1, len(payload) // 2)])

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "output"
            with mock.patch.object(noema.os, "write", side_effect=partial):
                noema._atomic_write(target, b"abcdefghij")
            self.assertGreater(calls, 1)
            self.assertEqual(target.read_bytes(), b"abcdefghij")

    def test_zero_write_refuses_and_leaks_no_temporary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with mock.patch.object(noema.os, "write", return_value=0), self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(directory / "output", b"x")
            self.assertEqual(raised.exception.code, "NOE-E-IO.WRITE")
            self.assertEqual(list(directory.iterdir()), [])

    def test_sync_failure_preserves_old_target_and_leaks_no_temporary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "output"
            target.write_bytes(b"old")
            with mock.patch.object(noema.os, "fsync", side_effect=OSError("fault")), self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(target, b"new")
            self.assertEqual(raised.exception.code, "NOE-E-IO.WRITE")
            self.assertEqual(target.read_bytes(), b"old")
            self.assertEqual([path.name for path in directory.iterdir()], ["output"])

    def test_replace_failure_preserves_old_target_and_leaks_no_temporary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "output"
            target.write_bytes(b"old")
            with mock.patch.object(noema.os, "replace", side_effect=OSError("fault")), self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(target, b"new")
            self.assertEqual(raised.exception.code, "NOE-E-IO.WRITE")
            self.assertEqual(target.read_bytes(), b"old")
            self.assertEqual([path.name for path in directory.iterdir()], ["output"])

    def test_maximum_leaf_name_succeeds_and_plus_one_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            exact = directory / ("a" * 255)
            noema._atomic_write(exact, b"x")
            self.assertEqual(exact.read_bytes(), b"x")
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(directory / ("b" * 256), b"x")
            self.assertEqual(raised.exception.code, "NOE-E-PATH.LEAF")

    def test_temporary_prefix_is_target_independent(self):
        real_mkstemp = tempfile.mkstemp
        observed = []

        def capture(*args, **kwargs):
            observed.append(kwargs.get("prefix"))
            return real_mkstemp(*args, **kwargs)

        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(noema.tempfile, "mkstemp", side_effect=capture):
                noema._atomic_write(Path(temporary) / "secret-target-name", b"x")
        self.assertEqual(observed, [".noema-write-"])


def _runtime_consequence_test(level, authorised):
    def test(self):
        effect = f"consequence{level}{'a' if authorised else 'u'}"
        consequence = [":", "core.consequence", str(level)]
        directive = [";", ["!", ["=", consequence, consequence]], ["+", [":", "effect", effect]]]
        authority = ()
        if authorised:
            directive = ["^", [":", "actor", "operator"], directive]
            authority = ("operator",)
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect, authority=authority),
        )
        result = noema.check_runtime(effect, [], manifest)
        expected = "permit" if level < 2 or authorised else "refuse"
        self.assertEqual((result["output"]["decision"], result["output"]["consequence"]), (expected, level))

    return test


for _level in range(4):
    for _authorised in (False, True):
        setattr(
            PolicyCheckTests,
            f"test_consequence_{_level}_{'authorised' if _authorised else 'unowned'}",
            _runtime_consequence_test(_level, _authorised),
        )


def _runtime_guard_test(operator, truth, expected):
    def test(self):
        effect = f"guard{operator == '/'}{truth}"
        proposition = ["core.checked", [":", "evidence", effect]]
        fact = checked_fact(proposition, truth, effect)
        consequence = [":", "core.consequence", "0"]
        directive = [
            operator,
            proposition,
            [";", ["!", ["=", consequence, consequence]], ["+", [":", "effect", effect]]],
        ]
        selection = runtime_selection(effect, facts=(fact,))
        _build, manifest, _projection = select_records(base_records(directive), selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], expected)

    return test


for _operator, _truth, _expected in (
    ("?", "true", "permit"),
    ("?", "false", "refuse"),
    ("?", "unknown", "unknown"),
    ("/", "true", "refuse"),
    ("/", "false", "permit"),
    ("/", "unknown", "unknown"),
):
    setattr(
        PolicyCheckTests,
        f"test_{'when' if _operator == '?' else 'unless'}_{_truth}",
        _runtime_guard_test(_operator, _truth, _expected),
    )


def _exception_cannot_authorize_test(expiry, scope, checked):
    def test(self):
        evidence = [":", "evidence", "exception"]
        gate = ["core.checked", evidence]
        facts = (checked_fact(gate, "true", "exception"),) if checked else ()
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "exception",
                "exception.only",
                [":", "actor", "admin"],
                gate,
                [":", "effect", "exceptional"],
                [":", "scope", scope],
                evidence,
                [":", "value", expiry],
                ["+", [":", "effect", "recover"]],
            ],
        ]
        selection = runtime_selection("exceptional", authority=("admin",), facts=facts)
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime("exceptional", selection["facts"], manifest)
        self.assertEqual((result["output"]["decision"], result["output"]["reason"]), ("refuse", "invalid-exception"))

    return test


for _name, _expiry, _scope, _checked in (
    ("missing_evidence", "active", "repository", False),
    ("expired", "expired", "repository", True),
    ("over_broad", "active", "other", True),
):
    setattr(
        PolicyCheckTests,
        f"test_exception_{_name}_cannot_mint_authority",
        _exception_cannot_authorize_test(_expiry, _scope, _checked),
    )


def _separation_fact_test(label):
    def test(self):
        effect = f"separate.{label}"
        consequence = [":", "core.consequence", "3"]
        directive = [";", ["!", ["=", consequence, consequence]], ["+", [":", "effect", effect]]]
        if label == "authority":
            proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", effect]]
        else:
            proposition = ["core.checked", [":", "evidence", label]]
        fact = checked_fact(proposition, "true", label)
        selection = runtime_selection(effect, authority=("operator",), facts=(fact,))
        _build, manifest, _projection = select_records(base_records(directive), selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual((result["output"]["decision"], result["output"]["reason"]), ("refuse", "default-deny"))

    return test


for _separation in ("capability", "authority", "done", "receipt", "verification"):
    setattr(
        PolicyCheckTests,
        f"test_{_separation}_does_not_imply_effect_authority",
        _separation_fact_test(_separation),
    )


def _runtime_literal_kind_test(kind, value):
    def test(self):
        encoded = value.encode("utf-8")
        literal = ["literal", f"lit.{kind}", kind, str(len(encoded)), value]
        directive = [
            ";",
            ["!", ["=", ["$", f"lit.{kind}"], ["$", f"lit.{kind}"]]],
            ["+", [":", "effect", f"read.{kind}"]],
        ]
        records = base_records(directive, literals=[literal])
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(f"read.{kind}"),
        )
        result = noema.literal_runtime(f"lit.{kind}", manifest)
        self.assertEqual((result["output"]["kind"], result["output"]["value"]), (kind, value))

    return test


for _runtime_kind, _runtime_value in {
    "id": "alpha",
    "path": "a/b",
    "sha256": "0" * 64,
    "command": "printf inert",
    "number": "123",
    "date": "2026-08-30",
    "url": "https://example.invalid/x",
    "quote": "say 'x'",
    "text": "plain text",
    "bytes": "00ff",
}.items():
    setattr(
        LiteralTests,
        f"test_runtime_literal_kind_{_runtime_kind}",
        _runtime_literal_kind_test(_runtime_kind, _runtime_value),
    )


def _transition_truth_test(truth, expected_status, expected_verdict):
    def test(self):
        proposition = ["core.checked", [":", "evidence", "gate"]]
        fact = checked_fact(proposition, truth, f"transition-{truth}")
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.move", ["+", [":", "effect", "move"]], source_binding()],
            ["transition", "transition.move", [":", "state", "machine"], [":", "state", "idle"], [":", "event", "go"], proposition, [":", "state", "ready"], ["+", [":", "effect", "move"]]],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("move", state="idle"),
        )
        result = noema.next_runtime("machine", "idle", "go", [fact], manifest)
        self.assertEqual((result["output"]["status"], result["verdict"]), (expected_status, expected_verdict))

    return test


for _truth, _status, _verdict in (
    ("true", "transition", "ok"),
    ("false", "stop", "ok"),
    ("unknown", "stop", "unknown"),
):
    setattr(
        TransitionTests,
        f"test_three_valued_guard_{_truth}",
        _transition_truth_test(_truth, _status, _verdict),
    )


def _literal_test(kind, value):
    def test(self):
        encoded = value.encode("utf-8")
        literal = ["literal", f"lit.{kind}", kind, str(len(encoded)), value]
        build, _artifacts = compile_records(base_records(literals=[literal]))
        self.assertEqual(build["graph"]["records"][1], literal)

    return test


for _kind, _value in {
    "id": "alpha",
    "path": "a/b",
    "sha256": "0" * 64,
    "command": "git status",
    "number": "123",
    "date": "2026-08-30",
    "url": "https://example.invalid/x",
    "quote": "say 'x'",
    "text": "plain text",
    "bytes": "00ff",
}.items():
    setattr(CanonicalSourceTests, f"test_literal_kind_{_kind}", _literal_test(_kind, _value))


def _core_type_test(type_name):
    def test(self):
        atom = [":", type_name, "x"]
        build, _artifacts = compile_records(base_records(["+", ["=", atom, atom]]))
        self.assertEqual(build["schema"], noema.BUILD_SCHEMA)

    return test


for _type_name in sorted(noema.CORE_TYPES):
    setattr(GraphValidationTests, f"test_core_type_{_type_name}", _core_type_test(_type_name))


def _operator_term(operator):
    proposition = ["core.ready", [":", "state", "ready"]]
    permit = ["+", proposition]
    atom = [":", "actor", "a"]
    finite = ["{}", "actor", atom]
    cases = {
        "!": ["!", proposition],
        "-": ["-", proposition],
        "+": permit,
        "?": ["?", proposition, permit],
        "/": ["/", proposition, permit],
        "@": ["@", [":", "scope", "repo"], permit],
        "^": ["^", [":", "actor", "owner"], permit],
        ";": [";", permit, ["-", proposition]],
        "&": ["+", ["&", proposition, proposition]],
        "|": ["+", ["|", proposition, proposition]],
        "~": ["+", ["~", proposition]],
        "=": ["+", ["=", atom, atom]],
        "=>": ["+", ["=>", proposition, proposition]],
        "all": ["+", ["all", ["x", "actor"], finite, ["=", ["%", "x"], atom]]],
        "any": ["+", ["any", ["x", "actor"], finite, ["=", ["%", "x"], atom]]],
        "one": ["+", ["one", ["x", "actor"], finite, ["=", ["%", "x"], atom]]],
        "in": ["+", ["in", atom, finite]],
        "subset": ["+", ["subset", finite, finite]],
        "lt": ["+", ["lt", [":", "value", "1"], [":", "value", "2"]]],
        "le": ["+", ["le", [":", "value", "1"], [":", "value", "2"]]],
        "gt": ["+", ["gt", [":", "value", "2"], [":", "value", "1"]]],
        "ge": ["+", ["ge", [":", "value", "2"], [":", "value", "1"]]],
        "count": ["+", ["=", ["count", finite], [":", "value", "1"]]],
    }
    return cases.get(operator)


def _operator_test(operator):
    def test(self):
        if operator == "<":
            definitions = [["definition", "local.order", [], ["<", [":", "state", "a"], [":", "state", "b"]]]]
            build, _artifacts = compile_records(base_records(definitions=definitions))
        else:
            build, _artifacts = compile_records(base_records(_operator_term(operator)))
        self.assertEqual(build["schema"], noema.BUILD_SCHEMA)

    return test


for _operator in sorted(noema.OPERATORS):
    safe_name = {"!": "require", "-": "prohibit", "+": "permit", "?": "when_true", "/": "when_false", "@": "scope", "^": "authority", ";": "sequence", "&": "and", "|": "or", "~": "not", "=": "equal", "=>": "implies", "<": "before"}.get(_operator, _operator)
    setattr(GraphValidationTests, f"test_operator_{safe_name}", _operator_test(_operator))


if __name__ == "__main__":
    unittest.main()
