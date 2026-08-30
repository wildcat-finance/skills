"""Scaffold and hostile-boundary tests for the Noema shadow prototype."""

from __future__ import annotations

from hashlib import sha256
import importlib.util
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


def load_noema():
    """Load the repository entrypoint without relying on import-path state."""
    spec = importlib.util.spec_from_file_location("noema_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


noema = load_noema()


def write_bytes(path: Path, payload: bytes) -> None:
    """Write one test-owned file below its disposable directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


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
            "29a63b93e77f4022d145520d2b29cfd52dbff55ff2d97a6568e8285d7ce67acc",
        )

    def test_repository_python_pin_is_exact(self):
        self.assertEqual((ROOT / ".python-version").read_text().strip(), "3.14.6")

    def test_schema_is_closed_and_names_all_record_families(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            set(schema), {"$schema", "$id", "title", "oneOf", "$defs"}
        )
        self.assertEqual(
            {"seedInventory", "lock", "manifest", "result", "evidence"},
            {
                reference["$ref"].rsplit("/", 1)[-1]
                for reference in schema["oneOf"]
            },
        )
        for name in ("seedInventory", "lock", "manifest", "result", "evidence"):
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


if __name__ == "__main__":
    unittest.main()
