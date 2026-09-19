"""Regression guards for public audit quotations rejected as key material."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import stat
import unittest


ROOT = Path(__file__).resolve().parents[3]
CONTROLLER = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
AUDIT_SOURCE = (
    "audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.md",
    376713,
    "bce008b201071b1ded3e656e24c0bfabb67923932a2cb3a994cb260172d6709c",
)
AUDIT_SYNOPSIS = (
    "audit/rounds/fiat-861-outer-checkpoint-archive-export-and-restore.synopsis.md",
    378244,
    "86bab9bce5db6b37a67527336bbfb1f65036a4f3ff504e50914be416be3934b2",
)


def public_fixture(specification: tuple[str, int, str]) -> bytes:
    """Read the pinned public bytes; custody failures remain test errors."""
    relative, length, digest = specification
    path = ROOT / relative
    if not stat.S_ISREG(path.lstat().st_mode):
        raise OSError(f"public fixture is not a regular file: {relative}")
    with path.open("rb") as stream:
        data = stream.read(length + 1)
    if len(data) != length or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"public fixture bytes differ from the capture: {relative}")
    return data


class PublicAuditQuotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        specification = importlib.util.spec_from_file_location(
            "checkpoint_marker_scan_hexctl", CONTROLLER
        )
        if specification is None or specification.loader is None:
            raise ImportError("checkpoint scanner controller cannot be loaded")
        cls.controller = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(cls.controller)

    def test_preserved_public_audit_source_is_not_key_material(self):
        data = public_fixture(AUDIT_SOURCE)
        self.assertFalse(
            self.controller._checkpoint_archive_secret_shaped(data),
            "the preserved public audit source contains quotations without key material",
        )

    def test_preserved_public_audit_synopsis_is_not_key_material(self):
        data = public_fixture(AUDIT_SYNOPSIS)
        self.assertFalse(
            self.controller._checkpoint_archive_secret_shaped(data),
            "the preserved public audit synopsis contains quotations without key material",
        )


if __name__ == "__main__":
    unittest.main()
