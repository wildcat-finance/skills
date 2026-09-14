"""Every assembly emitter in the fetched protocol source has exactly one fuzz case.

The two emitter files fetched from the pinned protocol commit declare `emit_<EventName>` free functions; the
harness suite declares `test_emit_<EventName>_<label>` fuzz cases. A Solidity
test cannot count the emitters without a filesystem read the harness profile
forbids, so the pairing count lives here, in the suite the root check map
already runs. A new emitter with no case, a case with no emitter, or a
duplicated case fails; nothing here writes. The emitter files are fetched by
`plugins/hexaemeron/harness/fetch_protocol.py`, so these tests skip until it has
run; the harness's forge checks run it first.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, os.pardir, "harness"))
EMITTER_FILES = (
    os.path.join(HARNESS, "src", "vendor", "libraries", "MarketEvents.sol"),
    os.path.join(HARNESS, "src", "vendor", "spherex", "SphereXProtectedEvents.sol"),
)
SUITE = os.path.join(HARNESS, "test", "EmitterFidelity.t.sol")
EMITTER_PATTERN = re.compile(r"^function emit_(\w+)\s*\(", re.MULTILINE)
CASE_PATTERN = re.compile(r"^\s*function test_emit_(\w+?)_(\w+)\s*\(", re.MULTILINE)
EXPECTED_EMITTERS = 27
FETCHED = all(os.path.isfile(path) for path in EMITTER_FILES)


def read(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")


def emitter_names():
    names = []
    for path in EMITTER_FILES:
        names.extend(EMITTER_PATTERN.findall(read(path)))
    return names


def case_names():
    return [name for name, _label in CASE_PATTERN.findall(read(SUITE))]


@unittest.skipUnless(FETCHED, "protocol source not fetched; run plugins/hexaemeron/harness/fetch_protocol.py")
class HarnessPairingTests(unittest.TestCase):
    def test_the_two_emitter_files_declare_the_pinned_emitter_count(self):
        self.assertEqual(len(emitter_names()), EXPECTED_EMITTERS)

    def test_the_case_count_equals_the_emitter_count(self):
        self.assertEqual(len(case_names()), len(emitter_names()))

    def test_every_emitter_has_exactly_one_case_and_no_case_is_orphaned(self):
        emitters = emitter_names()
        cases = case_names()
        self.assertEqual(sorted(cases), sorted(set(cases)), "a case is duplicated")
        self.assertEqual(sorted(emitters), sorted(set(emitters)), "an emitter is duplicated")
        self.assertEqual(sorted(cases), sorted(emitters))


if __name__ == "__main__":
    unittest.main()
