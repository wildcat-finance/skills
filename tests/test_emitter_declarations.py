import hashlib
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emitter_declarations.py"
STUDY = ROOT / "docs" / "emitter-declaration-check-study.md"
RUNBOOK = ROOT / "docs" / "emitter-declaration-check-runbook.md"

SPEC = importlib.util.spec_from_file_location("emitter_declarations", SCRIPT)
emitter_declarations = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(emitter_declarations)


class KeccakVectorTests(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(
            emitter_declarations.keccak256(b"").hex(),
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        )

    def test_erc20_transfer_signature(self):
        self.assertEqual(
            emitter_declarations.keccak256(b"Transfer(address,address,uint256)").hex(),
            "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        )

    def test_padding_boundary_vectors(self):
        # S1-R1-01: at len % 136 == 135 one padding byte remains, so the
        # suffix and the final bit share it as 0x81. Values from
        # `openssl dgst -keccak-256`.
        vectors = {
            135: "34367dc248bbd832f4e3e69dfaac2f92638bd0bbd18f2912ba4ef454919cf446",
            136: "a6c4d403279fe3e0af03729caada8374b5ca54d8065329a3ebcaeb4b60aa386e",
            271: "132f47effd6c8b1b299efa53fe68aece77ec8ae4eb2e294f668eec94f76001e1",
        }
        observed = {
            length: emitter_declarations.keccak256(b"a" * length).hex()
            for length in vectors
        }
        self.assertEqual(observed, vectors)

    def test_sponge_matches_sha3_across_three_blocks(self):
        # S1-R1-02: the sponge under SHA3's 0x06 suffix must equal hashlib's
        # SHA3-256 at every length from 0 to 409, which crosses the
        # one-byte-remaining boundary at 135, 271 and 407.
        sponge = getattr(emitter_declarations, "_sponge", None)
        self.assertIsNotNone(sponge, "no suffix-parameterised sponge to compare")
        mismatched = []
        for length in range(410):
            data = bytes(index % 251 for index in range(length))
            if sponge(data, 0x06) != hashlib.sha3_256(data).digest():
                mismatched.append(length)
        self.assertEqual(mismatched, [])


class SubcommandTests(unittest.TestCase):
    def test_build_and_check_refuse_until_implemented(self):
        for command in ("build", "check"):
            with self.subTest(command=command):
                self.assertEqual(emitter_declarations.main([command]), 2)


class SpecificationCopyTests(unittest.TestCase):
    def test_study_and_runbook_copies_are_committed(self):
        for path in (STUDY, RUNBOOK):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
