"""The checkpoint suite's host prerequisites hold under a closed fixed-tree run (#1927).

`done implement` runs the suite with a fixed PATH that puts the system
directories first and hides the user site. These guards keep that environment
from changing what the suite tests: a system LibreSSL must still yield the
profile's key form, and a missing schema oracle must refuse by name.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/fiat/scripts"))
from checkpoint_authority import signatures
import test_checkpoint_authority_records as records

# The directories hexctl's closed environment searches after the interpreter's.
CLOSED_DIRECTORIES = (
    *os.defpath.split(os.pathsep),
    "/usr/local/bin",
    "/opt/homebrew/bin",
    "/opt/local/bin",
)


def openssl_candidates():
    """Every distinct openssl a closed run or a pinned override could reach."""
    found = [os.environ.get("CHECKPOINT_OPENSSL", "")]
    found += [os.path.join(directory, "openssl") for directory in CLOSED_DIRECTORIES if directory]
    return sorted({str(Path(path).resolve()) for path in found if path and os.path.isfile(path)})


class ClosedRunPrerequisiteTests(unittest.TestCase):
    def test_every_reachable_openssl_writes_the_named_curve_key(self):
        candidates = openssl_candidates()
        self.assertTrue(candidates, "the checkpoint suite needs an openssl")
        with tempfile.TemporaryDirectory() as temporary:
            for openssl in candidates:
                with self.subTest(openssl=openssl):
                    path = Path(temporary) / "key.pem"
                    path.unlink(missing_ok=True)
                    subprocess.run([openssl, *records.P256_KEYGEN, "-out", str(path)],
                                   check=True, capture_output=True, timeout=10)
                    data = subprocess.check_output(
                        [openssl, "pkey", "-in", str(path), "-pubout", "-outform", "DER"],
                        timeout=10)
                    self.assertEqual(91, len(data))
                    self.assertTrue(data.startswith(signatures.SPKI_PREFIX))

    def test_a_missing_schema_oracle_refuses_by_name(self):
        with mock.patch.dict(sys.modules, {"jsonschema": None}), \
             self.assertRaisesRegex(AssertionError,
                                    r"mandatory schema tool absent: jsonschema; install "
                                    r"plugins/hexaemeron/tests/requirements\.lock"):
            records.SchemaTests.setUpClass()


if __name__ == "__main__":
    unittest.main()
